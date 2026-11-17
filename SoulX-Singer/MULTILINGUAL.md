# Indian-language extension

The frontend accepts native Hindi, Punjabi, Haryanvi, Bengali, Tamil, Telugu,
Kannada, Malayalam, Marathi, Gujarati, Urdu, Odia and Assamese scripts. It emits
language-tagged, broad IPA-like phones and syllable boundaries for note alignment.
Romanized Indic lyrics are intentionally rejected: they are ambiguous and are not
English phonemes. Convert them to the correct native script before submitting.

`/phonemize` supports `language: "auto"`; automatic detection is script based.
Devanagari and Bengali-script languages are ambiguous by design, so specify Hindi vs
Marathi/Haryanvi and Bengali vs Assamese when that distinction matters.

## API

Legacy API usage remains unchanged. For a trained Indic model, set both variables
before starting the server:

```powershell
$env:SOULX_INDIC_MODEL = "C:\models\soulx-indic-finetuned.pt"
$env:SOULX_INDIC_MANIFEST = "C:\models\manifest.json"
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

The manifest must include `{"trained_languages":["Hindi", ...]}` only after
held-out native-listener pronunciation evaluation. Then submit ordinary SoulX
note metadata with `language`, `text`, `duration`, `note_pitch` and `note_type`;
the server generates the phonemes and supports `control: "score"` or `"melody"`.
The service returns HTTP 409 instead of synthetic audio when no validated Indic
checkpoint is configured.

For low memory inference use CUDA fp16, 3–8 second segments and 12–20 diffusion
steps after validating quality. The stock model and optional Indic model are loaded
side-by-side by this small API; on a 4 GB GPU serve only one model/process at a
time or use CPU/offloading.
