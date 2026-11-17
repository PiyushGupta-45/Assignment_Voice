import os
import re
import shutil
import tempfile
from pathlib import Path

_FILENAME = re.compile(r"^[a-f0-9]{64}\.mp3$")


class LocalAudioService:
    """Constrained local persistence for generated cache-key MP3 files."""

    def __init__(self, root: Path):
        self.root = root.resolve()

    @property
    def ready(self) -> bool:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            return self.root.is_dir()
        except OSError:
            return False

    @staticmethod
    def filename(cache_key: str) -> str:
        name = f"{cache_key}.mp3"
        if not _FILENAME.fullmatch(name):
            raise ValueError("Invalid local audio filename")
        return name

    def path_for_filename(self, filename: str) -> Path:
        if not _FILENAME.fullmatch(filename):
            raise ValueError("Invalid local audio filename")
        path = (self.root / filename).resolve()
        if path.parent != self.root:
            raise ValueError("Invalid local audio path")
        return path

    def save(self, source: Path, cache_key: str) -> tuple[str, str]:
        if not source.is_file() or source.stat().st_size == 0:
            raise ValueError("Final MP3 is missing or empty")
        if not self.ready:
            raise RuntimeError("Local audio storage is unavailable")
        filename = self.filename(cache_key)
        destination = self.path_for_filename(filename)
        # Copy through an adjacent temporary file, then atomically publish only this key's file.
        with tempfile.NamedTemporaryFile(dir=self.root, prefix=".upload-", suffix=".tmp", delete=False) as temporary:
            temp_path = Path(temporary.name)
        try:
            shutil.copyfile(source, temp_path)
            if temp_path.stat().st_size == 0:
                raise ValueError("Local MP3 copy is empty")
            os.replace(temp_path, destination)
        finally:
            temp_path.unlink(missing_ok=True)
        return filename, str(Path("generated_songs") / filename).replace("\\", "/")

    def exists(self, filename: str) -> bool:
        try:
            return self.path_for_filename(filename).is_file()
        except ValueError:
            return False
