from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    groq_api_key: str | None = None
    groq_model: str | None = None
    sarvam_api_key: str | None = None
    sarvam_tts_model: str = "bulbul:v4-flash"
    sarvam_voice: str | None = None
    firebase_storage_bucket: str | None = None
    google_application_credentials: Path | None = None
    prompt_version: str = "v1"
    audio_bitrate: str = "64k"
    voice_volume: float = 1.0
    background_volume: float = 0.18
    sarvam_pace: float = 1.0
    sarvam_timeout_seconds: float = 45
    groq_timeout_seconds: float = 30
    groq_temperature: float = 0.6
    groq_max_tokens: int = 160
    groq_reasoning_effort: str | None = None
    supported_languages: str = "Hindi,English,Bengali,Tamil,Telugu,Kannada,Malayalam,Marathi,Gujarati,Punjabi,Odia"
    groq_cost_per_million_tokens_inr: float = 0
    sarvam_cost_per_1000_chars_inr: float = 0
    signed_url_ttl_minutes: int = 60
    music_root: Path = Path("assets/music")
    local_audio_root: Path = Path("generated_songs")
    audio_mix_version: str = "v3-balanced-music"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"

    @property
    def language_names(self) -> set[str]:
        return {x.strip() for x in self.supported_languages.split(",") if x.strip()}

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
