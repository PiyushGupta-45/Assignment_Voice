
import os
import json
import io
import threading
import os
from pathlib import Path

import torch
import numpy as np
import soundfile as sf

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from soulxsinger.utils.file_utils import load_config
from soulxsinger.models.soulxsinger import SoulXSinger
from soulxsinger.utils.data_processor import DataProcessor
from soulxsinger.text.indic import (SUPPORTED_LANGUAGES, canonical_language,
                                    detect_language, normalize_text, phonemize_notes)


BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "pretrained_models" / "SoulX-Singer" / "model.pt"
CONFIG_PATH = BASE_DIR / "soulxsinger" / "config" / "soulxsinger.yaml"
PHONESET_PATH = BASE_DIR / "soulxsinger" / "utils" / "phoneme" / "phone_set.json"

PROMPT_WAV_PATH = BASE_DIR / "example" / "audio" / "en_prompt.mp3"
PROMPT_METADATA_PATH = BASE_DIR / "example" / "audio" / "en_prompt.json"

DEVICE = "cpu"
INDIC_MODEL_PATH = Path(os.environ.get("SOULX_INDIC_MODEL", "")) if os.environ.get("SOULX_INDIC_MODEL") else None

app = FastAPI(title="SoulX-Singer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None
config = None
data_processor = None
prompt_data = None
indic_model = None

# Prevent simultaneous inference requests on this CPU setup.
inference_lock = threading.Lock()


class GenerateRequest(BaseModel):
    target_metadata: list[dict] = Field(min_length=1)
    language: str = "auto"
    control: str = "score"
    auto_shift: bool = True
    pitch_shift: int = 0


class PhonemizeRequest(BaseModel):
    lyrics: str = Field(min_length=1)
    language: str = "auto"


def _resolved_language(text: str, requested: str) -> str:
    selected = canonical_language(requested)
    return detect_language(text) if selected == "auto" else selected


def _trained_languages() -> set[str]:
    """Read an explicit fine-tuning manifest; never infer support from labels."""
    manifest = os.environ.get("SOULX_INDIC_MANIFEST", "")
    if not manifest or not Path(manifest).is_file():
        return set()
    try:
        return set(json.loads(Path(manifest).read_text(encoding="utf-8")).get("trained_languages", []))
    except (json.JSONDecodeError, OSError):
        return set()


@app.get("/languages")
def languages():
    trained = _trained_languages()
    return {"languages": [{"name": name, "code": code,
                            "acoustic_model_trained": name in trained or name in {"English", "Mandarin", "Cantonese"}}
                           for name, code in SUPPORTED_LANGUAGES.items()]}


@app.post("/phonemize")
def phonemize(request: PhonemizeRequest):
    language = _resolved_language(request.lyrics, request.language)
    text = normalize_text(request.lyrics, language)
    words = text.split()
    if language in {"English", "Mandarin", "Cantonese"}:
        # Existing frontend is note-oriented; leave legacy phonemization to metadata creation.
        return {"language": language, "text": text, "words": words, "legacy_frontend": True}
    phones = phonemize_notes(words, language)
    return {"language": language, "text": text, "words": words, "phonemes": phones,
            "acoustic_model_trained": language in _trained_languages()}


@app.on_event("startup")
def load_singer_model():
    global model, config, data_processor, prompt_data, indic_model

    required_files = [
        MODEL_PATH,
        CONFIG_PATH,
        PHONESET_PATH,
        PROMPT_WAV_PATH,
        PROMPT_METADATA_PATH,
    ]

    for path in required_files:
        if not path.is_file():
            raise RuntimeError(f"Required file missing: {path}")

    print("Loading SoulX-Singer model...")

    config = load_config(str(CONFIG_PATH))

    model = SoulXSinger(config).to(DEVICE)

    checkpoint = torch.load(
        str(MODEL_PATH),
        map_location="cpu",
        weights_only=False,
    )

    model.load_state_dict(checkpoint["state_dict"], strict=True)
    model.eval()

    # An optional independently fine-tuned checkpoint can be served alongside
    # legacy synthesis. It is never synthesized with the base EN/ZH/YUE model.
    if INDIC_MODEL_PATH:
        if not INDIC_MODEL_PATH.is_file():
            raise RuntimeError(f"SOULX_INDIC_MODEL does not exist: {INDIC_MODEL_PATH}")
        indic_config = load_config(str(CONFIG_PATH))
        indic_config.model.encoder.vocab_size = int(indic_config.multilingual.vocab_size)
        indic_model = SoulXSinger(indic_config).to(DEVICE)
        indic_checkpoint = torch.load(str(INDIC_MODEL_PATH), map_location="cpu", weights_only=False)
        indic_model.load_state_dict(indic_checkpoint["state_dict"], strict=True)
        indic_model.eval()

    data_processor = DataProcessor(
        hop_size=config.audio.hop_size,
        sample_rate=config.audio.sample_rate,
        phoneset_path=str(PHONESET_PATH),
        device=DEVICE,
    )

    with open(PROMPT_METADATA_PATH, "r", encoding="utf-8") as f:
        prompt_metadata = json.load(f)

    if not prompt_metadata:
        raise RuntimeError("Prompt metadata is empty")

    prompt_data = data_processor.process(
        prompt_metadata[0],
        str(PROMPT_WAV_PATH),
    )

    print("SoulX-Singer API ready!")


@app.get("/health")
def health():
    return {
        "status": "ready" if model is not None else "loading",
        "model": "SoulX-Singer",
        "device": DEVICE,
    }


@app.post("/generate")
def generate_song(request: GenerateRequest):

    if model is None:
        raise HTTPException(503, "Model is not loaded")

    if request.control not in ("score", "melody"):
        raise HTTPException(400, "Control must be score or melody")

    targets = [dict(x) for x in request.target_metadata]
    requested_language = canonical_language(request.language)
    for target in targets:
        text = target.get("text", "")
        language = _resolved_language(text, requested_language) if text else requested_language
        if language == "auto":
            raise HTTPException(400, "language=auto requires text in every target segment")
        target["language"] = language
        if language not in {"English", "Mandarin", "Cantonese"}:
            if language not in _trained_languages() or indic_model is None:
                raise HTTPException(409, f"{language} frontend is available, but no pronunciation-validated multilingual checkpoint is configured. Set SOULX_INDIC_MANIFEST only after fine-tuning and evaluation.")
            if not text:
                raise HTTPException(400, "Indian-language generation requires native-script text")
            words = normalize_text(text, language).split()
            target["text"] = " ".join(words)
            target["phoneme"] = " ".join(phonemize_notes(words, language))
        required = ("duration", "phoneme", "note_pitch", "note_type", "time")
        missing = [key for key in required if key not in target]
        if missing:
            raise HTTPException(400, f"Target metadata missing: {', '.join(missing)}")
        lengths = [len(str(target[key]).split()) for key in ("duration", "phoneme", "note_pitch", "note_type")]
        if len(set(lengths)) != 1:
            raise HTTPException(400, "text/phoneme, duration, note_pitch and note_type must be note-aligned")

    try:
        last_time = targets[-1]["time"][1]
        generated_len = int(
            last_time / 1000 * config.audio.sample_rate
        )

        if generated_len <= 0:
            raise ValueError("Invalid target duration")

        generated_merged = np.zeros(
            generated_len,
            dtype=np.float32,
        )

        with inference_lock:
            for target_meta in targets:

                start = int(
                    target_meta["time"][0]
                    / 1000
                    * config.audio.sample_rate
                )

                end = int(
                    target_meta["time"][1]
                    / 1000
                    * config.audio.sample_rate
                )

                if start < 0 or end <= start or end > generated_len:
                    raise ValueError("Invalid segment time")

                target_data = data_processor.process(
                    target_meta,
                    None,
                )

                infer_data = {
                    "prompt": prompt_data,
                    "target": target_data,
                }

                active_model = indic_model if target_meta.get("language") not in {"English", "Mandarin", "Cantonese"} else model
                with torch.inference_mode():
                    generated_audio = active_model.infer(
                        infer_data,
                        auto_shift=request.auto_shift,
                        pitch_shift=request.pitch_shift,
                        n_steps=config.infer.n_steps,
                        cfg=config.infer.cfg,
                        control=request.control,
                        use_fp16=False,
                    )

                audio = generated_audio.squeeze().cpu().numpy()

                if audio.ndim != 1:
                    raise ValueError("Unexpected generated audio shape")

                length = min(
                    len(audio),
                    generated_len - start,
                )

                generated_merged[start:start + length] = audio[:length]

        audio_buffer = io.BytesIO()

        sf.write(
            audio_buffer,
            generated_merged,
            config.audio.sample_rate,
            format="WAV",
        )

        audio_buffer.seek(0)

        return StreamingResponse(
            audio_buffer,
            media_type="audio/wav",
            headers={
                "Content-Disposition": 'attachment; filename="generated.wav"'
            },
        )

    except Exception as e:
        print("Generation error:", repr(e))
        raise HTTPException(500, str(e))
