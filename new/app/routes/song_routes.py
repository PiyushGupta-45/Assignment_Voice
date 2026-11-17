import asyncio
import logging
import tempfile
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import FileResponse
from app.models.song_models import GenerateSongRequest, SongMetadata, SongResponse
from app.services.cache_service import cache_key
from app.services.cost_service import log_estimated_cost
from app.utils.audio_utils import audio_duration_seconds
from app.utils.validation import LANGUAGE_CODES, validate_language

router = APIRouter(tags=["songs"]); log = logging.getLogger(__name__)

def app_services(request: Request): return request.app.state.settings, request.app.state.firebase, request.app.state.groq, request.app.state.sarvam, request.app.state.music, request.app.state.mixer, request.app.state.local_audio


def local_audio_url(request: Request, filename: str) -> str:
    return f"{str(request.base_url).rstrip('/')}/audio/{filename}"


async def cached_audio_url(request: Request, song: dict) -> str:
    """Resolve both new local metadata and older Firebase-backed cache records safely."""
    _, firebase, _, _, _, _, local_audio = app_services(request)
    storage_type = song.get("storage_type")
    audio_path = song.get("audio_path")
    if storage_type == "local":
        filename = Path(str(audio_path or "")).name
        if local_audio.exists(filename):
            return local_audio_url(request, filename)
        raise HTTPException(410, "Cached song metadata exists but its local audio file is unavailable.")
    if storage_type == "firebase" or (audio_path and str(audio_path).startswith("songs/")):
        if not firebase.storage_ready:
            raise HTTPException(410, "Cached song uses Firebase Storage, which is currently unavailable.")
        return await asyncio.to_thread(firebase.audio_url, audio_path)
    raise HTTPException(410, "Cached song has no accessible audio file.")

@router.post("/generate-song", response_model=SongResponse, status_code=status.HTTP_201_CREATED)
async def generate_song(body: GenerateSongRequest, request: Request):
    settings, firebase, groq, sarvam, music, mixer, local_audio = app_services(request)
    try: language = validate_language(body.language, settings.language_names)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    key = cache_key(body.name, language, body.style, settings)
    try:
        existing = await asyncio.to_thread(firebase.get, key)
        if existing and existing.get("status") == "completed":
            url = await cached_audio_url(request, existing)
            return SongResponse(cached=True, cache_key=key, name=body.name, language=language, style=body.style, lyrics=existing["lyrics"], audio_url=url)
        claimed = await asyncio.to_thread(firebase.claim, key, {"name":body.name, "language":language, "style":body.style, "prompt_version":settings.prompt_version, "tts_model":settings.sarvam_tts_model, "voice":settings.sarvam_voice or "default"})
        if not claimed: raise HTTPException(409, "A song with these settings is already processing; retry shortly.")
        lyrics_result = await asyncio.to_thread(groq.generate, body.name, language, body.style)
        with tempfile.TemporaryDirectory(prefix="song-") as temporary:
            root = Path(temporary); voice, final = root / "voice.wav", root / "song.mp3"
            await asyncio.to_thread(sarvam.synthesize, lyrics_result.lines, LANGUAGE_CODES[language], voice)
            track = await asyncio.to_thread(music.select, body.style, key)
            await asyncio.to_thread(mixer.mix, track, voice, final)
            if firebase.storage_ready:
                try:
                    path = await asyncio.to_thread(firebase.upload, final, key)
                    storage_type = "firebase"
                    url = await asyncio.to_thread(firebase.audio_url, path)
                except Exception as exc:
                    # Storage is optional: a credential/bucket failure must not discard valid audio.
                    log.warning("Firebase Storage upload failed; using local audio storage: %s", type(exc).__name__)
                    filename, path = await asyncio.to_thread(local_audio.save, final, key)
                    storage_type, url = "local", local_audio_url(request, filename)
            else:
                filename, path = await asyncio.to_thread(local_audio.save, final, key)
                storage_type, url = "local", local_audio_url(request, filename)
            duration = await asyncio.to_thread(audio_duration_seconds, final)
        metadata = {"lyrics":lyrics_result.lines, "audio_path":path, "audio_url":url, "storage_type":storage_type, "audio_format":"mp3", "duration_seconds":duration}
        await asyncio.to_thread(firebase.complete, key, metadata)
        log_estimated_cost(settings, len("\n".join(lyrics_result.lines)), lyrics_result.prompt_tokens, lyrics_result.completion_tokens)
        return SongResponse(cached=False, cache_key=key, name=body.name, language=language, style=body.style, lyrics=lyrics_result.lines, audio_url=url)
    except HTTPException: raise
    except Exception as exc:
        log.exception("Song generation failed for cache key %s", key)
        await asyncio.to_thread(firebase.fail, key, str(exc))
        raise HTTPException(502, "Song generation failed. Check server configuration and try again.") from exc

@router.get("/songs/{cache_key}", response_model=SongMetadata)
async def get_song(cache_key: str, request: Request):
    if len(cache_key) != 64 or any(c not in "0123456789abcdef" for c in cache_key): raise HTTPException(422, "Invalid cache key")
    data = await asyncio.to_thread(request.app.state.firebase.get, cache_key)
    if not data: raise HTTPException(404, "Song not found")
    return SongMetadata(cache_key=cache_key, **data)


@router.get("/audio/{filename}")
async def download_local_audio(filename: str, request: Request):
    try:
        path = request.app.state.local_audio.path_for_filename(filename)
    except ValueError as exc:
        raise HTTPException(404, "Audio file not found") from exc
    if not path.is_file():
        raise HTTPException(404, "Audio file not found")
    return FileResponse(path, media_type="audio/mpeg", filename=filename, content_disposition_type="inline")
