from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

Style = Literal["happy", "romantic", "birthday", "friendship", "energetic"]


class GenerateSongRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=60, examples=["Rahul"])
    language: str = Field(min_length=1, max_length=30, examples=["Hindi"])
    style: Style = "happy"

    @field_validator("name")
    @classmethod
    def safe_name(cls, value: str) -> str:
        if not value or not any(char.isalpha() for char in value):
            raise ValueError("name must contain at least one letter")
        if any(char in value for char in "{}[]<>`\\\n\r"):
            raise ValueError("name contains unsupported characters")
        return " ".join(value.split())


class SongResponse(BaseModel):
    success: bool = True
    cached: bool
    cache_key: str
    name: str
    language: str
    style: Style
    lyrics: list[str]
    audio_url: str
    audio_format: str = "mp3"


class SongMetadata(BaseModel):
    cache_key: str
    name: str
    language: str
    style: str
    lyrics: list[str] | None = None
    audio_path: str | None = None
    audio_url: str | None = None
    storage_type: str | None = None
    status: str
    audio_format: str = "mp3"
