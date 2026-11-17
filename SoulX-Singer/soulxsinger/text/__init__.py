"""Text frontends used to create SoulX-Singer note metadata."""

from .indic import (SUPPORTED_LANGUAGES, detect_language, normalize_text,
                    phonemize_notes, phonemize_word)

__all__ = ["SUPPORTED_LANGUAGES", "detect_language", "normalize_text", "phonemize_notes", "phonemize_word"]
