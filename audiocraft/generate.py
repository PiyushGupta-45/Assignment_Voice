import torch
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write

print("Loading MusicGen Small...")

model = MusicGen.get_pretrained("facebook/musicgen-small")
model.set_generation_params(duration=8)

print("Generating Hip-Hop Beat...")

wav = model.generate([
    "Dark hip hop instrumental, deep 808 bass, "
    "trap drums, crisp hi hats, cinematic atmosphere"
])

audio_write(
    "my_first_beat",
    wav[0].cpu(),
    model.sample_rate
)

print("Song generated: my_first_beat.wav")