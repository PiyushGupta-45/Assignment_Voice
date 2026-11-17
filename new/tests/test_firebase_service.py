from app.config import Settings
from app.services.firebase_service import FirebaseService


def test_firestore_initializes_without_storage_bucket(monkeypatch):
    fake_db = object()
    monkeypatch.setattr("app.services.firebase_service.get_app", lambda: object())
    monkeypatch.setattr("app.services.firebase_service.firestore.client", lambda: fake_db)
    service = FirebaseService(Settings(firebase_storage_bucket=None))
    assert service.firestore_ready is True
    assert service.storage_ready is False
    assert service.db is fake_db
    assert service.storage_error == "FIREBASE_STORAGE_BUCKET is not configured"
