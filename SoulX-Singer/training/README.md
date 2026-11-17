# Multilingual training

The released model has no Indian-language acoustic training. `upgrade_checkpoint.py`
creates an initialization only; it must not be used to claim pronunciation support.

Prepare consented, license-compatible *singing* recordings with word/note alignment,
native-script lyrics, F0 and MIDI/score timing. Run:

```powershell
python training/prepare_multilingual.py corpus.jsonl validated.jsonl
python training/upgrade_checkpoint.py --base pretrained_models/SoulX-Singer/model.pt --output pretrained_models/SoulX-Singer-Indic/model-init.pt
```

Fine-tune the 4096-vocabulary model using the original authors' unreleased training
objective (this repository exposes inference only). Train the new embedding rows plus
the text encoder first, then jointly fine-tune decoder/vocoder with held-out native
speaker pronunciation evaluation. For 4 GB VRAM: 24 kHz clips <= 6 s, batch size 1,
gradient accumulation 16, fp16/bf16, gradient checkpointing and frozen vocoder;
full-quality joint training normally needs 16–24 GB VRAM.

Potential sources must be checked per release: AI4Bharat/MUCS and IndicVoices are
speech resources, not automatically usable singing data; OpenSLR/Indic corpora have
their own licenses. Obtain explicit performer/vocal rights, song/lyric rights, and
phoneme-or-note alignment consent. Do not train from commercial recordings without
rights. Evaluate each language with native listeners and held-out singer/song splits.
