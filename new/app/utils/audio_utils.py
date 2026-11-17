import subprocess
from pathlib import Path


def ffmpeg_available() -> bool:
    try:
        return subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5, check=False).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def audio_duration_seconds(path: Path) -> float | None:
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)], capture_output=True, text=True, check=True, timeout=10)
        return round(float(result.stdout.strip()), 3)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
