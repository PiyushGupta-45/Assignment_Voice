import base64
import time
from pathlib import Path
import httpx
from app.config import Settings


class SarvamTTSService:
    endpoint = "https://api.sarvam.ai/text-to-speech"
    def __init__(self, settings: Settings): self.settings = settings

    def synthesize(self, lines: list[str], language_code: str, output_path: Path) -> None:
        if not self.settings.sarvam_api_key:
            raise RuntimeError("Sarvam is not configured. Set SARVAM_API_KEY.")
        payload = {"text": "\n".join(lines), "language_code": language_code, "model": self.settings.sarvam_tts_model, "pace": self.settings.sarvam_pace, "speech_sample_rate": 22050, "output_audio_codec": "wav"}
        if self.settings.sarvam_voice: payload["speaker"] = self.settings.sarvam_voice
        headers = {"api-subscription-key": self.settings.sarvam_api_key, "Content-Type": "application/json"}
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = httpx.post(self.endpoint, json=payload, headers=headers, timeout=self.settings.sarvam_timeout_seconds)
                if response.status_code == 429 or response.status_code >= 500:
                    response.raise_for_status()
                response.raise_for_status()
                audios = response.json().get("audios")
                if not isinstance(audios, list) or not audios or not isinstance(audios[0], str): raise ValueError("Sarvam response has no audio")
                output_path.write_bytes(base64.b64decode(audios[0], validate=True))
                if output_path.stat().st_size < 64: raise ValueError("Sarvam returned empty audio")
                return
            except (httpx.HTTPError, ValueError, KeyError) as exc:
                last_error = exc
                if attempt < 2: time.sleep(0.5 * (2 ** attempt))
        raise RuntimeError("Sarvam text-to-speech failed.") from last_error
