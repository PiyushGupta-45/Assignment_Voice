import logging
import uuid
from datetime import timedelta
from pathlib import Path
from firebase_admin import credentials, firestore, initialize_app, storage, get_app
from app.config import Settings

log = logging.getLogger(__name__)


class FirebaseService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.db = None
        self.bucket = None
        self.firestore_error: str | None = None
        self.storage_error: str | None = None
        try:
            try: get_app()
            except ValueError:
                # pydantic reads .env without exporting it to os.environ, so load the
                # local service account explicitly. Cloud Run continues to use ADC.
                credential = credentials.Certificate(str(settings.google_application_credentials)) if settings.google_application_credentials else None
                initialize_app(credential=credential)
            self.db = firestore.client()
        except Exception as exc:
            self.firestore_error = f"Firestore initialization failed: {type(exc).__name__}"
            log.warning(self.firestore_error)
        if not settings.firebase_storage_bucket:
            self.storage_error = "FIREBASE_STORAGE_BUCKET is not configured"
            return
        try:
            self.bucket = storage.bucket(settings.firebase_storage_bucket)
        except Exception as exc:
            self.storage_error = f"Firebase Storage initialization failed: {type(exc).__name__}"
            log.warning(self.storage_error)

    @property
    def firestore_ready(self) -> bool: return self.db is not None
    @property
    def storage_ready(self) -> bool: return self.bucket is not None
    @property
    def ready(self) -> bool: return self.firestore_ready
    @property
    def error(self) -> str | None: return self.firestore_error
    def require_firestore(self) -> None:
        if not self.firestore_ready: raise RuntimeError(self.firestore_error or "Firestore is unavailable")
    def require_storage(self) -> None:
        if not self.storage_ready: raise RuntimeError(self.storage_error or "Firebase Storage is unavailable")
    def get(self, key: str) -> dict | None:
        self.require_firestore(); snapshot = self.db.collection("songs").document(key).get()
        return snapshot.to_dict() if snapshot.exists else None
    def claim(self, key: str, metadata: dict) -> bool:
        """Atomically reserves an absent/failed document. Never replaces completed work."""
        self.require_firestore(); ref = self.db.collection("songs").document(key)
        transaction = self.db.transaction()
        @firestore.transactional
        def reserve(txn):
            current = ref.get(transaction=txn)
            if current.exists and current.to_dict().get("status") in {"processing", "completed"}: return False
            txn.set(ref, {**metadata, "status":"processing", "created_at": firestore.SERVER_TIMESTAMP}, merge=True)
            return True
        return reserve(transaction)
    def complete(self, key: str, metadata: dict) -> None:
        self.require_firestore(); self.db.collection("songs").document(key).set({**metadata, "status":"completed", "completed_at":firestore.SERVER_TIMESTAMP}, merge=True)
    def fail(self, key: str, message: str) -> None:
        if self.firestore_ready: self.db.collection("songs").document(key).set({"status":"failed", "error":message[:500], "failed_at":firestore.SERVER_TIMESTAMP}, merge=True)
    def upload(self, local_path: Path, key: str) -> str:
        self.require_storage(); path = f"songs/{key}.mp3"; blob = self.bucket.blob(path)
        blob.metadata = {"generator":"personalized-song-generator", "format":"mp3"}
        blob.upload_from_filename(str(local_path), content_type="audio/mpeg")
        return path
    def audio_url(self, audio_path: str) -> str:
        self.require_storage(); blob = self.bucket.blob(audio_path)
        try: return blob.generate_signed_url(expiration=timedelta(minutes=self.settings.signed_url_ttl_minutes), method="GET")
        except Exception as exc:
            # Firebase download tokens are bearer-style permanent URLs; only use if explicitly generated here.
            token = str(uuid.uuid4()); blob.metadata = {**(blob.metadata or {}), "firebaseStorageDownloadTokens":token}; blob.patch()
            return f"https://firebasestorage.googleapis.com/v0/b/{self.bucket.name}/o/{audio_path.replace('/', '%2F')}?alt=media&token={token}"
