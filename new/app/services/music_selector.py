from pathlib import Path
from app.config import Settings

AUDIO_EXTENSIONS = {".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"}


class MusicSelector:
    def __init__(self, settings: Settings): self.root = settings.music_root
    def select(self, style: str, cache_key: str) -> Path:
        for folder in (self.root / style, self.root / "default"):
            tracks = sorted(p for p in folder.glob("*") if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS) if folder.exists() else []
            if tracks: return tracks[int(cache_key[:8], 16) % len(tracks)]
        raise FileNotFoundError(f"No licensed music track for '{style}'. Add an audio file under {self.root / style} or {self.root / 'default'}.")
