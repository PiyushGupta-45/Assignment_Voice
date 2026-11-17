import hashlib
from app.config import Settings
from app.utils.validation import normalize_name


def cache_key(name: str, language: str, style: str, settings: Settings) -> str:
    fields = [normalize_name(name), language.casefold(), style, settings.prompt_version, settings.sarvam_tts_model, settings.sarvam_voice or "default", settings.audio_mix_version]
    return hashlib.sha256("|".join(fields).encode("utf-8")).hexdigest()
