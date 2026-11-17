import re

LANGUAGE_CODES = {"Hindi":"hi-IN", "English":"en-IN", "Bengali":"bn-IN", "Tamil":"ta-IN", "Telugu":"te-IN", "Kannada":"kn-IN", "Malayalam":"ml-IN", "Marathi":"mr-IN", "Gujarati":"gu-IN", "Punjabi":"pa-IN", "Odia":"od-IN"}
STYLES = {"happy", "romantic", "birthday", "friendship", "energetic"}


def validate_language(language: str, allowed: set[str]) -> str:
    canonical = next((item for item in allowed if item.casefold() == language.strip().casefold()), None)
    if canonical is None or canonical not in LANGUAGE_CODES:
        raise ValueError(f"Unsupported language '{language}'. Supported: {', '.join(sorted(allowed))}")
    return canonical


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).casefold()


def validate_lyrics(lines: object) -> list[str]:
    if not isinstance(lines, list) or len(lines) != 4:
        raise ValueError("Lyrics must contain exactly four lines")
    clean = []
    for line in lines:
        if not isinstance(line, str):
            raise ValueError("Each lyric line must be text")
        line = " ".join(line.strip().split())
        if not line or len(line) > 80:
            raise ValueError("Lyric lines must be between 1 and 80 characters")
        clean.append(line)
    if len("\n".join(clean)) > 200:
        raise ValueError("Lyrics are too long")
    return clean
