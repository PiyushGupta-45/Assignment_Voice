import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routes.song_routes import router
from app.services.audio_mixer import AudioMixer
from app.services.firebase_service import FirebaseService
from app.services.groq_service import GroqLyricsService
from app.services.music_selector import MusicSelector
from app.services.sarvam_service import SarvamTTSService
from app.services.local_audio_service import LocalAudioService
from app.utils.audio_utils import ffmpeg_available

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
app = FastAPI(title="Personalized Song Generator", version="1.0.0")
settings = get_settings()
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=False, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type"])
app.state.settings = settings; app.state.firebase = FirebaseService(settings); app.state.groq = GroqLyricsService(settings); app.state.sarvam = SarvamTTSService(settings); app.state.music = MusicSelector(settings); app.state.mixer = AudioMixer(settings); app.state.local_audio = LocalAudioService(settings.local_audio_root)
app.include_router(router)

@app.get("/health")
async def health():
    ffmpeg = ffmpeg_available(); firestore = app.state.firebase.firestore_ready; storage = app.state.firebase.storage_ready; local_audio = app.state.local_audio.ready
    return {"status":"ok" if ffmpeg and firestore and local_audio else "degraded", "fastapi_status":"ok", "ffmpeg_available":ffmpeg, "firestore_initialized":firestore, "firestore_error":app.state.firebase.firestore_error, "firebase_storage_initialized":storage, "firebase_storage_error":app.state.firebase.storage_error, "local_audio_storage_available":local_audio}
