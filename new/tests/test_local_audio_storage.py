from pathlib import Path
import pytest
from app.services.local_audio_service import LocalAudioService


def test_local_mp3_saving_is_scoped_to_cache_key(tmp_path):
    source = tmp_path / "mixed.mp3"; source.write_bytes(b"mp3-data")
    storage = LocalAudioService(tmp_path / "generated_songs")
    key = "a" * 64
    filename, audio_path = storage.save(source, key)
    assert filename == f"{key}.mp3"
    assert audio_path == f"generated_songs/{filename}"
    assert storage.path_for_filename(filename).read_bytes() == b"mp3-data"

@pytest.mark.parametrize("filename", ["../secret.mp3", "song.mp3", "a" * 64 + ".wav", "A" * 64 + ".mp3"])
def test_invalid_local_audio_filename_is_rejected(tmp_path, filename):
    with pytest.raises(ValueError):
        LocalAudioService(tmp_path).path_for_filename(filename)
