from pathlib import Path
import pytest
from app.config import Settings
from app.services.audio_mixer import AudioMixer
from app.services.music_selector import MusicSelector

def test_ffmpeg_command_is_argument_list():
    mixer = AudioMixer(Settings())
    # command duration probing is covered by integration paths; keep this unit
    # test focused on the safe argument/filter construction.
    import app.services.audio_mixer as module
    original = module.audio_duration_seconds
    module.audio_duration_seconds = lambda _: 3.0
    try:
        cmd = mixer.command(Path("music.mp3"), Path("voice.wav"), Path("out.mp3"))
    finally:
        module.audio_duration_seconds = original
    graph = cmd[cmd.index("-filter_complex") + 1]
    assert cmd[0] == "ffmpeg" and "threshold=0.12:ratio=4" in graph and "asplit=2[voice][voice_sidechain]" in graph and "aformat=channel_layouts=stereo" in graph and "loudnorm=I=-14" in graph and cmd[cmd.index("-t") + 1] == "3.0"
def test_missing_music_has_clear_fallback_error(tmp_path):
    with pytest.raises(FileNotFoundError): MusicSelector(Settings(music_root=tmp_path)).select("happy", "a" * 64)
