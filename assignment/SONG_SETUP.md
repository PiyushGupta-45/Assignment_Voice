# NameTune: FastAPI personalized-song backend

The app sends a name and selected language to the FastAPI backend. Groq, Sarvam,
FFmpeg, Firebase, and all API keys remain on the backend.

## App configuration

Set only the public backend URL in this project's `.env`:

```text
# Android Emulator
EXPO_PUBLIC_SONG_API_URL=http://10.0.2.2:8000

# Physical Android device connected by USB (run `adb reverse` below)
# EXPO_PUBLIC_SONG_API_URL=http://127.0.0.1:8000

# Physical Android device (replace with this computer's LAN IP)
# EXPO_PUBLIC_SONG_API_URL=http://192.168.x.x:8000
```

Start the Python backend from `C:\Users\pgupt\OneDrive\Desktop\new` so Android can reach it:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then restart Expo or rebuild the Android app. NameTune calls `POST /generate-song`
and plays the returned `audio_url` with its existing Expo audio player.

For a USB-connected physical Android device, forward the backend port before
starting/reloading the app:

```powershell
adb reverse tcp:8000 tcp:8000
```

For production, deploy the backend with HTTPS and use its HTTPS URL instead of
cleartext local HTTP.
