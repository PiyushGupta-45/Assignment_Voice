# Personalized Song Generator

A production-oriented FastAPI backend that creates a four-line personalized musical greeting: Groq writes the lyrics, Sarvam Bulbul v4 Flash narrates them, FFmpeg mixes narration over your licensed instrumental, and Firebase stores the MP3 and metadata.

Ordinary TTS is rhythmic narration, not claimed to be singing or beat-synchronised rap.

## Architecture

`POST /generate-song` validates the request, calculates a cache key, then checks Firestore **before any AI call**. On a miss it reserves a `processing` document, generates exactly four validated lines, synthesizes WAV audio, selects a local style track, and mixes it to a 64 kbps MP3. If Firebase Storage is configured and usable, it uploads there; otherwise it saves `generated_songs/{cache_key}.mp3`. Cache hits return the stored lyrics and an accessible URL without regenerating them. Concurrent identical work receives `409` while its reservation is active; incomplete results are never served.

## Prerequisites

- Python 3.11+ and FFmpeg (which includes `ffprobe`)
- A Groq API key and a current model ID from the [Groq model list](https://console.groq.com/docs/models)
- Sarvam API key and a compatible Bulbul v4 Flash persona (or omit `SARVAM_VOICE` to use Sarvam's documented default)
- Firebase project with Firestore and Cloud Storage

## Local setup

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Install FFmpeg with your package manager (for example, `winget install Gyan.FFmpeg` on Windows, `brew install ffmpeg` on macOS, or `sudo apt install ffmpeg` on Debian/Ubuntu). Fill `.env`, then run:

```bash
uvicorn app.main:app --reload
pytest
```

`GET /health` starts without paid API calls. It reports `degraded` until FFmpeg and Firebase are configured. It will never print secrets.

## Required environment variables

Fill these values in `.env`:

```dotenv
GROQ_API_KEY=...
GROQ_MODEL=...                 # select an available low-cost JSON-capable model
SARVAM_API_KEY=...
SARVAM_TTS_MODEL=bulbul:v4-flash
SARVAM_VOICE=...               # valid v4 persona or blank for provider default
FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\local-service-account.json
```

`FIREBASE_STORAGE_BUCKET` is optional. Without it, Firestore remains enabled and final MP3s are stored in `generated_songs/` and served through `GET /audio/{filename}`. Optionally set `LOCAL_AUDIO_ROOT` to relocate that directory. All settings and optional cost estimates appear in [.env.example](.env.example). Do not commit `.env` or a service-account JSON file. `GOOGLE_APPLICATION_CREDENTIALS` is for local use; on Cloud Run use Application Default Credentials through the service account.

## Firebase setup

1. Create/select a Firebase project and enable **Cloud Firestore** (Native mode) and **Cloud Storage**.
2. Copy the Storage bucket name to `FIREBASE_STORAGE_BUCKET`. Firebase Storage availability/billing depends on your project and region; check the current [Firebase pricing](https://firebase.google.com/pricing) and enable Blaze if required.
3. For local development, create a minimally privileged service account, download its JSON outside this repository, set `GOOGLE_APPLICATION_CREDENTIALS`, and grant Firestore read/write plus Storage object create/read permissions.
4. For Cloud Run, grant those roles to the Cloud Run runtime service account. Cloud Run uses ADC; do not ship a JSON key in the image.
5. Storage is optional for local development. When configured and supported by credentials, the app emits 60-minute signed URLs. If signing is unavailable it falls back to a Firebase download token URL. That token functions as a long-lived bearer secret; use bucket rules, rotation, or a signing-capable deployment for stronger access control.

## Add licensed music

Put royalty-free, licensed, or owned instrumentals into `assets/music/happy/`, `romantic/`, `birthday/`, `friendship/`, or `energetic/`. Add `assets/music/default/` for a fallback. No music files are bundled. See [assets/music/README.md](assets/music/README.md).

## Generate a song

```bash
curl -X POST "http://localhost:8000/generate-song" \
  -H "Content-Type: application/json" \
  -d '{"name":"Rahul","language":"Hindi","style":"happy"}'
```

Typical response:

```json
{"success":true,"cached":false,"cache_key":"...","name":"Rahul","language":"Hindi","style":"happy","lyrics":["...","...","...","..."],"audio_url":"https://...","audio_format":"mp3"}
```

Retrieve non-secret metadata with `GET /songs/{cache_key}`. The endpoint does not return a URL because URLs are intentionally time-bound/generated on demand.

## Cost and reliability

The system limits lyrics, tokens, and retries; it reuses local music and its Firestore cache. Set the optional per-token and per-character INR estimates in `.env` and the service logs a request estimate. This is an engineering target, not a price guarantee; it excludes Cloud Run, Firebase storage/bandwidth, and music licensing. Update estimates when provider rates change.

External APIs are covered by mocks/configuration tests, not live keys. Before production, use a valid Groq model and Sarvam v4 persona from their current docs, add an authorized Firebase service account, and put licensed music in each style directory. The Sarvam REST integration follows its documented base64 `audios` response and uses `api-subscription-key`.

## Cloud Run

```bash
gcloud builds submit --tag REGION-docker.pkg.dev/PROJECT/REPOSITORY/personalized-song
gcloud run deploy personalized-song --image REGION-docker.pkg.dev/PROJECT/REPOSITORY/personalized-song --region REGION --service-account SONG_RUNTIME_SA --set-secrets GROQ_API_KEY=GROQ_API_KEY:latest,SARVAM_API_KEY=SARVAM_API_KEY:latest --set-env-vars GROQ_MODEL=YOUR_MODEL,FIREBASE_STORAGE_BUCKET=YOUR_BUCKET
```

Grant `SONG_RUNTIME_SA` its Firestore/Storage permissions first and configure Cloud Run authentication to match your client. The Docker image installs FFmpeg, runs as a non-root user, reads `PORT`, and does not copy `.env` or service keys.

## Common errors

- `degraded` health: install FFmpeg or configure Firebase credentials/bucket.
- `No licensed music track`: add an audio file to the selected style or `default` folder.
- `Groq is not configured` / `Sarvam is not configured`: fill the keys and `GROQ_MODEL`.
- HTTP `409`: an identical request is currently generating; retry shortly.
- HTTP `502`: inspect non-sensitive server logs; failed cache documents retain a bounded error detail for troubleshooting.
