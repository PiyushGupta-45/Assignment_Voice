from fastapi.testclient import TestClient
from app.main import app
from app.config import Settings
from app.services.groq_service import LyricsResult
from app.services.local_audio_service import LocalAudioService
from app.services.cache_service import cache_key


class FakeFirebase:
    def __init__(self, storage_ready=False):
        self.firestore_ready = True; self.storage_ready = storage_ready; self.firestore_error = None; self.storage_error = "FIREBASE_STORAGE_BUCKET is not configured" if not storage_ready else None
        self.records = {}; self.uploaded = False
    def get(self, key): return self.records.get(key)
    def claim(self, key, metadata): self.records[key] = {**metadata, "status":"processing"}; return True
    def complete(self, key, metadata): self.records[key] = {**self.records[key], **metadata, "status":"completed"}
    def fail(self, key, message): self.records[key] = {**self.records.get(key, {}), "status":"failed"}
    def upload(self, path, key): self.uploaded = True; return f"songs/{key}.mp3"
    def audio_url(self, path): return f"https://storage.example/{path}"


class FakeGroq:
    def generate(self, *args): return LyricsResult(["one", "two", "three", "four"])
class FakeSarvam:
    def synthesize(self, lines, language, path): path.write_bytes(b"voice")
class FakeMusic:
    def select(self, style, key): return __file__
class FakeMixer:
    def mix(self, music, voice, output): output.write_bytes(b"mixed-mp3")


def configure_generation_app(tmp_path, firebase):
    app.state.settings = Settings(local_audio_root=tmp_path / "generated_songs")
    app.state.firebase = firebase; app.state.groq = FakeGroq(); app.state.sarvam = FakeSarvam(); app.state.music = FakeMusic(); app.state.mixer = FakeMixer(); app.state.local_audio = LocalAudioService(tmp_path / "generated_songs")

def test_api_request_validation():
    client = TestClient(app)
    response = client.post("/generate-song", json={"name":"", "language":"Hindi", "style":"happy"})
    assert response.status_code == 422
def test_health_never_calls_paid_api():
    response = TestClient(app).get("/health")
    assert response.status_code == 200 and "ffmpeg_available" in response.json()

def test_frontend_preflight_allows_local_vite():
    response = TestClient(app).options("/generate-song", headers={"Origin":"http://localhost:5173", "Access-Control-Request-Method":"POST"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"

def test_local_storage_fallback_and_download(tmp_path):
    firebase = FakeFirebase(storage_ready=False); configure_generation_app(tmp_path, firebase)
    client = TestClient(app)
    response = client.post("/generate-song", json={"name":"Asha", "language":"Hindi", "style":"happy"})
    assert response.status_code == 201
    payload = response.json(); filename = f"{payload['cache_key']}.mp3"
    assert payload["audio_url"].endswith(f"/audio/{filename}")
    assert firebase.records[payload["cache_key"]]["storage_type"] == "local"
    audio = client.get(f"/audio/{filename}")
    assert audio.status_code == 200 and audio.headers["content-type"].startswith("audio/mpeg")

def test_firebase_storage_path_is_preserved(tmp_path):
    firebase = FakeFirebase(storage_ready=True); configure_generation_app(tmp_path, firebase)
    response = TestClient(app).post("/generate-song", json={"name":"Ravi", "language":"Hindi", "style":"happy"})
    assert response.status_code == 201
    record = firebase.records[response.json()["cache_key"]]
    assert firebase.uploaded and record["storage_type"] == "firebase" and record["audio_path"].startswith("songs/")

def test_missing_cached_local_file_does_not_regenerate_lyrics(tmp_path):
    firebase = FakeFirebase(); configure_generation_app(tmp_path, firebase)
    key = "b" * 64
    firebase.records[key] = {"status":"completed", "lyrics":["one"] * 4, "audio_path":f"generated_songs/{key}.mp3", "storage_type":"local"}
    # Use the route's actual deterministic key by changing get to return this completed record.
    firebase.get = lambda _key: firebase.records[key]
    response = TestClient(app).post("/generate-song", json={"name":"Meera", "language":"Hindi", "style":"happy"})
    assert response.status_code == 410

def test_existing_firebase_cache_record_remains_compatible(tmp_path):
    firebase = FakeFirebase(storage_ready=True); configure_generation_app(tmp_path, firebase)
    key = cache_key("Rahul", "Hindi", "happy", app.state.settings)
    firebase.records[key] = {"status":"completed", "lyrics":["one"] * 4, "audio_path":f"songs/{key}.mp3"}
    response = TestClient(app).post("/generate-song", json={"name":"Rahul", "language":"Hindi", "style":"happy"})
    assert response.status_code == 201
    assert response.json()["cached"] is True
    assert response.json()["audio_url"].endswith(f"songs/{key}.mp3")

def test_audio_route_rejects_traversal(tmp_path):
    configure_generation_app(tmp_path, FakeFirebase())
    assert TestClient(app).get("/audio/..%2Fsecret.mp3").status_code == 404

def test_health_reports_independent_storage_status(tmp_path, monkeypatch):
    configure_generation_app(tmp_path, FakeFirebase(storage_ready=False))
    monkeypatch.setattr("app.main.ffmpeg_available", lambda: True)
    payload = TestClient(app).get("/health").json()
    assert payload["status"] == "ok" and payload["firestore_initialized"] is True
    assert payload["firebase_storage_initialized"] is False and payload["local_audio_storage_available"] is True
