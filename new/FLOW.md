# Personalized Song Generator: Complete Flow

Yeh document `C:\Users\pgupt\OneDrive\Desktop\new` backend ka current end-to-end flow explain karta hai.

## High-level flow

```text
React Native App
       |
       | POST /generate-song
       v
FastAPI Backend (app/routes/song_routes.py)
       |
       +--> Firestore cache check
       |       |
       |       +--> Cache hit: existing lyrics + MP3 URL return
       |
       +--> Groq: four personalized lyric lines
       |
       +--> Sarvam Bulbul v4 Flash: lyrics -> raw WAV voice
       |
       +--> Local licensed music track selection
       |
       +--> FFmpeg: voice + background music -> final MP3
       |
       +--> Firebase Storage upload, or generated_songs/ fallback
       |
       +--> Firestore completed metadata save
       |
       +--> JSON response with lyrics and audio_url
       v
React Native audio player
```

## 1. Incoming request

Main endpoint:

```http
POST /generate-song
Content-Type: application/json
```

Example request:

```json
{
  "name": "Rahul",
  "language": "Hindi",
  "style": "birthday"
}
```

Route file: `app/routes/song_routes.py`.

Request validation `app/models/song_models.py` mein hoti hai:

- Name trim hota hai aur empty/unsafe input reject hota hai.
- Name maximum 60 characters ka hai.
- Supported style: `happy`, `romantic`, `birthday`, `friendship`, `energetic`.
- Language configured language list se validate hoti hai.
- Validated language Sarvam BCP-47 code mein map hoti hai; Hindi -> `hi-IN`.

## 2. Cache key aur Firestore cache

File: `app/services/cache_service.py`

Backend deterministic SHA-256 cache key banata hai from:

```text
normalized name + language + style + prompt version + TTS model + voice + audio mix version
```

Current audio mix version cache key mein intentionally included hai. Isse mixer settings change hone ke baad old MP3 cache return nahi hota.

Firestore collection:

```text
songs/{cache_key}
```

Cache document `completed` ho aur audio accessible ho, toh Groq, Sarvam aur FFmpeg dobara call nahi hote. Existing lyrics aur `audio_url` return hota hai.

Concurrent requests ke liye Firestore transaction document ko `processing` state mein claim karti hai. Same generation while processing request ko `409` milta hai.

## 3. Groq lyrics generation

File: `app/services/groq_service.py`

Request Groq OpenAI-compatible endpoint ko jaati hai via official `groq` Python SDK.

Required config:

```dotenv
GROQ_API_KEY=...
GROQ_MODEL=openai/gpt-oss-20b
GROQ_MAX_TOKENS=512
GROQ_REASONING_EFFORT=low
```

Groq prompt exactly 4 short personalized, rhythmic lines maangta hai. `openai/gpt-oss-20b` ke liye first attempt strict JSON Schema mode mein hota hai:

```json
{"lines":["line 1","line 2","line 3","line 4"]}
```

Fallback JSON-object mode limited retry ke liye hai. Response `validate_lyrics` se validate hota hai: exactly four non-empty text lines.

## 4. Sarvam voice generation

File: `app/services/sarvam_service.py`

Lyrics four lines ek single text mein join hote hain aur Sarvam endpoint ko jaate hain:

```text
POST https://api.sarvam.ai/text-to-speech
```

Main headers/payload:

```text
api-subscription-key: SARVAM_API_KEY
model: bulbul:v4-flash
language_code: hi-IN
output_audio_codec: wav
```

Sarvam response base64 audio deta hai. Backend usse temporary `voice.wav` mein decode karta hai aur empty response reject karta hai.

Required config:

```dotenv
SARVAM_API_KEY=...
SARVAM_TTS_MODEL=bulbul:v4-flash
SARVAM_VOICE=            # optional valid v4 persona
```

## 5. Background music selection

File: `app/services/music_selector.py`

AI music generation nahi hota. Backend local licensed assets use karta hai:

```text
assets/music/birthday/birthday-instrumental.mp3
```

Style request `birthday` ho toh birthday folder se deterministic track pick hota hai. Agar requested style folder empty ho, `assets/music/default/` fallback check hota hai. Koi track na mile toh song generation failure return hota hai; fake music/audio generate nahi hota.

## 6. FFmpeg mixing

File: `app/services/audio_mixer.py`

Inputs:

```text
Input 0: background instrumental MP3
Input 1: Sarvam raw WAV voice
```

Mixer workflow:

1. Voice aur music dono 48 kHz stereo format mein convert hote hain.
2. Voice loudness normalize hoti hai (`-14 LUFS` target) aur voice stream `asplit=2` se split hoti hai.
3. First voice branch final mix mein jaati hai.
4. Second branch sidechain signal banti hai aur voice bolte waqt music ko gently duck karti hai.
5. Background volume current config se controlled hai; upper mixer cap `0.28` hai.
6. `amix` voice aur ducked music combine karta hai.
7. `alimiter` clipping avoid karta hai.
8. `-t <voice_duration>` final MP3 ko exact narration duration tak trim karta hai.
9. Output MP3 `libmp3lame`, `64k` bitrate par encode hota hai.

Important fix: voice stream ko sidechain aur final mix dono mein use karne ke liye `asplit` compulsory hai. Iske bina sidechain stream consume hone se final output mein voice unreliable/missing ho sakti hai.

Relevant config:

```dotenv
AUDIO_BITRATE=64k
VOICE_VOLUME=1.0
BACKGROUND_VOLUME=1
```

`BACKGROUND_VOLUME=1` ka actual final gain mixer safety cap ke baad maximum `0.28` hota hai. Isse voice clear aur music audible dono rehte hain.

## 7. Audio storage

### Preferred: Firebase Storage

File: `app/services/firebase_service.py`

Firebase Storage configured aur accessible ho toh final MP3 upload hota hai:

```text
songs/{cache_key}.mp3
```

Backend signed URL generate karne ki try karta hai. Signed URL unsupported ho toh Firebase download-token URL fallback hota hai.

### Local fallback

Firebase Storage unavailable/upload fail ho toh final MP3 local save hota hai:

```text
generated_songs/{cache_key}.mp3
```

Local output browser/mobile app ke liye serve hota hai:

```http
GET /audio/{cache_key}.mp3
```

Filename strict SHA-256 + `.mp3` format mein validate hota hai, so path traversal possible nahi hai.

## 8. Firestore metadata

Final generation complete hone par `songs/{cache_key}` mein metadata save hota hai:

```json
{
  "status": "completed",
  "lyrics": ["...", "...", "...", "..."],
  "audio_path": "generated_songs/<cache_key>.mp3",
  "audio_url": "http://host/audio/<cache_key>.mp3",
  "storage_type": "local",
  "audio_format": "mp3",
  "duration_seconds": 14.86
}
```

Firebase Storage use hone par `storage_type` `firebase` aur `audio_path` `songs/<cache_key>.mp3` hota hai.

## 9. Final API response

```json
{
  "success": true,
  "cached": false,
  "cache_key": "sha256-key",
  "name": "Rahul",
  "language": "Hindi",
  "style": "birthday",
  "lyrics": ["Line 1", "Line 2", "Line 3", "Line 4"],
  "audio_url": "http://127.0.0.1:8000/audio/sha256-key.mp3",
  "audio_format": "mp3"
}
```

## 10. React Native app connection

React Native app folder:

```text
C:\Users\pgupt\OneDrive\Desktop\assignment
```

File `assignment/songApi.js` directly calls:

```text
POST {EXPO_PUBLIC_SONG_API_URL}/generate-song
```

For a USB-connected Android device:

```dotenv
EXPO_PUBLIC_SONG_API_URL=http://127.0.0.1:8000
```

Then run:

```powershell
adb reverse tcp:8000 tcp:8000
```

Phone ka `127.0.0.1:8000` USB ke through computer ke FastAPI port `8000` tak forward hota hai.

## 11. Start commands

Backend:

```powershell
cd C:\Users\pgupt\OneDrive\Desktop\new
C:\Users\pgupt\miniconda3\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

React Native app:

```powershell
cd C:\Users\pgupt\OneDrive\Desktop\assignment
npm run android
```

## 12. Important current limitations

- `birthday` instrumental currently available hai. Other styles ke liye licensed tracks corresponding folders mein add karne padenge.
- Firebase Storage bucket unavailable ho toh local fallback works; app ko backend URL accessible hona chahiye.
- Laptop/backend off hone par local URL based mobile app song generate nahi kar sakti. Permanent standalone use ke liye backend Cloud Run/HTTPS deployment required hai.
- No API secret React Native app mein nahi hona chahiye. Secrets sirf `new/.env` backend mein rehte hain.
