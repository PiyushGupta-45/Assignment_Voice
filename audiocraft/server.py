
import io
import torch
import soundfile as sf

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from audiocraft.models import MusicGen

app = FastAPI()

print("Loading MusicGen...")
model = MusicGen.get_pretrained(
    "facebook/musicgen-small",
    device="cuda"
)
print("MusicGen loaded successfully!")

class MusicRequest(BaseModel):
    prompt: str

@app.post("/generate")
def generate_music(request: MusicRequest):
    model.set_generation_params(duration=15)

    with torch.inference_mode():
        wav = model.generate([request.prompt])

    audio_buffer = io.BytesIO()

    sf.write(
        audio_buffer,
        wav[0].cpu().numpy().T,
        model.sample_rate,
        format="WAV"
    )

    audio_buffer.seek(0)

    return StreamingResponse(
        audio_buffer,
        media_type="audio/wav",
        headers={
            "Content-Disposition": "attachment; filename=music.wav"
        }
    )

@app.get("/")
def home():
    return {"message": "MusicGen API is running!"}
