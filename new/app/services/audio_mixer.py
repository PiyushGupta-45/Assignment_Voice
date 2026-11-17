import subprocess
from pathlib import Path
from app.config import Settings
from app.utils.audio_utils import audio_duration_seconds


class AudioMixer:
    def __init__(self, settings: Settings): self.settings = settings
    def command(self, music: Path, voice: Path, output: Path) -> list[str]:
        # Force both sources into the same stereo/sample-rate format before
        # mixing. Sarvam returns mono WAV while background tracks are usually
        # stereo; normalizing the summed streams could otherwise mask speech.
        # Voice is normalized independently and music remains audible below it.
        music_volume = min(self.settings.background_volume, 0.28)
        graph = (
            "[1:a]aresample=48000,aformat=channel_layouts=stereo,"
            f"volume={self.settings.voice_volume * 1.25},loudnorm=I=-14:TP=-1.5:LRA=7,asplit=2[voice][voice_sidechain];"
            "[0:a]aresample=48000,aformat=channel_layouts=stereo,"
            f"volume={music_volume}[bg];"
            # Gentle ducking: the previous low threshold continuously muted
            # the music beneath narration.
            "[bg][voice_sidechain]sidechaincompress=threshold=0.12:ratio=4:attack=30:release=180[ducked];"
            "[voice][ducked]amix=inputs=2:duration=first:weights='1 1':normalize=0,alimiter=limit=0.95[out]"
        )
        voice_duration = audio_duration_seconds(voice)
        if voice_duration is None or voice_duration <= 0:
            raise RuntimeError("Could not determine voice audio duration.")
        # -stream_loop supports brief music assets. Explicit -t prevents an
        # infinite loop and guarantees final audio ends with the narration.
        return ["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(music), "-i", str(voice), "-filter_complex", graph, "-map", "[out]", "-t", str(voice_duration), "-c:a", "libmp3lame", "-b:a", self.settings.audio_bitrate, str(output)]
    def mix(self, music: Path, voice: Path, output: Path) -> None:
        try:
            result = subprocess.run(self.command(music, voice, output), capture_output=True, text=True, timeout=120, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc: raise RuntimeError("FFmpeg could not process audio.") from exc
        if result.returncode != 0 or not output.exists() or output.stat().st_size == 0:
            raise RuntimeError("FFmpeg audio mixing failed.")
