# Hugging Face AI lyrics setup

The app calls a secure Cloudflare Worker. It keeps the Hugging Face token off the phone. Never put an `hf_...` token in the mobile app `.env`.

## 1. Create a Hugging Face token

In Hugging Face **Settings → Access Tokens**, create a fine-grained token with **Make calls to Inference Providers** permission. Copy it once and keep it private.

## 2. Deploy the included Worker

From the project root:

```powershell
cd worker
npx wrangler login
npx wrangler secret put HF_TOKEN
npx wrangler deploy
```

When prompted for `HF_TOKEN`, paste the Hugging Face token. Wrangler prints a URL such as `https://nametune-lyrics-ai.<your-subdomain>.workers.dev`.

## 3. Connect the mobile app

In the project-root `.env`, add the deploy URL with `/generate`:

```env
EXPO_PUBLIC_LYRICS_AI_URL=https://nametune-lyrics-ai.your-subdomain.workers.dev/generate
```

Restart Expo after saving:

```powershell
npx expo start --clear
```

## Cost and safety controls

- Each request is limited to five lyric lines and 150 output tokens.
- The Worker has a basic six-requests-per-minute-per-IP guard. For a public production app, also configure Cloudflare WAF/rate limiting and Firebase App Check.
- Hugging Face Inference Providers free accounts have limited monthly credits, not unlimited AI generation. Avoid adding a payment method if you want generation to stop after those credits are exhausted.
- When the Worker URL is absent or unavailable, the app uses its local lyric variations instead.
