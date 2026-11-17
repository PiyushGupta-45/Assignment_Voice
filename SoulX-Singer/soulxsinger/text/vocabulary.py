"""Additional, language-tagged phoneme tokens for multilingual fine-tuning."""
from .indic import SUPPORTED_LANGUAGES

# Every symbol emitted by indic.py is listed here. Tags keep acoustically similar
# phones separable across languages until fine-tuning learns useful sharing.
INDIC_PHONES = (
    "a aː ə i iː u uː e eː o oː ɔ ai au oi ou r̩ "
    "k kʰ g gʱ ŋ t͡ʃ t͡ʃʰ d͡ʒ d͡ʒʱ ɲ ʈ ʈʰ ɖ ɖʱ ɳ t̪ t̪ʰ d̪ d̪ʱ n "
    "p pʰ b bʱ m j r l ʋ ʃ ʂ s ɦ h ̃ x z ʒ ʔ ɣ f q ɽ ɭ ɻ"
).split()
INDIC_LANGUAGE_CODES = tuple(v for k, v in SUPPORTED_LANGUAGES.items()
                             if k not in {"English", "Mandarin", "Cantonese"})
MULTILINGUAL_PHONEMES = tuple(f"{lang}_{phone}" for lang in INDIC_LANGUAGE_CODES for phone in INDIC_PHONES)

def extend_phone_map(phone2idx: dict[str, int]) -> dict[str, int]:
    """Append tokens without changing any legacy IDs/checkpoint compatibility."""
    for phone in MULTILINGUAL_PHONEMES:
        phone2idx.setdefault(phone, len(phone2idx))
    return phone2idx
