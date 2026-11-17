"""Validate aligned multilingual singing manifests before GPU training.

Input JSONL rows must contain wav_path, language, text, phoneme, duration,
note_pitch, note_type and either f0 (melody training) or notes (score training).
All durations/notes are note-aligned; native-script text is retained for audit.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from soulxsinger.text.indic import canonical_language, phonemize_notes
from soulxsinger.text.vocabulary import MULTILINGUAL_PHONEMES

def validate(row: dict) -> dict:
    lang = canonical_language(row["language"])
    text = row["text"].split()
    phones = row.get("phoneme", "").split()
    if not phones: phones = phonemize_notes(text, lang)
    tokens = lambda value: value.split() if isinstance(value, str) else [str(x) for x in value]
    fields = {"text": text, "phoneme": phones, "duration": tokens(row["duration"]),
              "note_pitch": tokens(row["note_pitch"]), "note_type": tokens(row["note_type"])}
    lengths = {k: len(v) for k,v in fields.items()}
    if len(set(lengths.values())) != 1: raise ValueError(f"unaligned row: {lengths}")
    if lang not in {"English","Mandarin","Cantonese"} and any(p != "<SP>" and not p.startswith((lang_code + "_" for lang_code in ["hi","pa","hr","bn","ta","te","kn","ml","mr","gu","ur","or","as"])) for p in phones):
        raise ValueError("Indian-language row contains non-native frontend tokens")
    row["language"], row["phoneme"] = lang, " ".join(phones)
    return row

def main():
    p=argparse.ArgumentParser(); p.add_argument("input"); p.add_argument("output"); args=p.parse_args()
    rows=[]
    for n,line in enumerate(Path(args.input).read_text(encoding="utf-8").splitlines(), 1):
        try: rows.append(validate(json.loads(line)))
        except Exception as e: raise SystemExit(f"row {n}: {e}")
    Path(args.output).write_text("\n".join(json.dumps(x,ensure_ascii=False) for x in rows)+"\n", encoding="utf-8")
    print(f"validated {len(rows)} rows; added vocabulary size: {len(MULTILINGUAL_PHONEMES)}")
if __name__ == "__main__": main()
