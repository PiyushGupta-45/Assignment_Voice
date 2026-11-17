"""Native-script Indic text normalisation and deterministic phonemisation.

This is deliberately a phonemic frontend, not an English/ARPAbet approximation.
The output is an auditable broad IPA-like inventory encoded as ``<lang>_<phone>``.
It is suitable for creating aligned training data.  A frontend alone does *not*
make an acoustic checkpoint multilingual; callers must use a fine-tuned model.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Iterable

SUPPORTED_LANGUAGES = {
    "English": "en", "Mandarin": "zh", "Cantonese": "yue",
    "Hindi": "hi", "Punjabi": "pa", "Haryanvi": "hr", "Bengali": "bn",
    "Tamil": "ta", "Telugu": "te", "Kannada": "kn", "Malayalam": "ml",
    "Marathi": "mr", "Gujarati": "gu", "Urdu": "ur", "Odia": "or", "Assamese": "as",
}
_ALIASES = {x.lower(): x for x in SUPPORTED_LANGUAGES}
_ALIASES.update({"auto": "auto", "odia": "Odia", "oriya": "Odia", "bangla": "Bengali"})

# Unicode blocks are preferable to statistical guessing: lyrics can be very short.
_BLOCKS = {
    "Hindi": (0x0900, 0x097F), "Marathi": (0x0900, 0x097F), "Haryanvi": (0x0900, 0x097F),
    "Punjabi": (0x0A00, 0x0A7F), "Bengali": (0x0980, 0x09FF), "Assamese": (0x0980, 0x09FF),
    "Gujarati": (0x0A80, 0x0AFF), "Odia": (0x0B00, 0x0B7F), "Tamil": (0x0B80, 0x0BFF),
    "Telugu": (0x0C00, 0x0C7F), "Kannada": (0x0C80, 0x0CFF), "Malayalam": (0x0D00, 0x0D7F),
    "Urdu": (0x0600, 0x06FF),
}
_DIGITS = {chr(base + digit): str(digit) for base in
           (0x0966, 0x09E6, 0x0A66, 0x0AE6, 0x0B66, 0x0BE6, 0x0C66, 0x0CE6, 0x0D66)
           for digit in range(10)}

# Indic orthographies are mostly abugidas.  This map preserves contrastive
# dental/retroflex and aspirated consonants required by Indian-language singing.
_VOWELS = {"अ":"a","आ":"aː","इ":"i","ई":"iː","उ":"u","ऊ":"uː","ऋ":"r̩","ए":"eː","ऐ":"ai","ओ":"oː","औ":"au",
 "ा":"aː","ि":"i","ी":"iː","ु":"u","ू":"uː","ृ":"r̩","े":"eː","ै":"ai","ो":"oː","ौ":"au",
 "অ":"ɔ","আ":"a","ই":"i","ঈ":"iː","উ":"u","ঊ":"uː","এ":"e","ঐ":"oi","ও":"o","ঔ":"ou","া":"a","ি":"i","ী":"iː","ু":"u","ূ":"uː","ে":"e","ৈ":"oi","ো":"o","ৌ":"ou",
 "અ":"ə","આ":"aː","ઇ":"i","ઈ":"iː","ઉ":"u","ઊ":"uː","એ":"eː","ઐ":"ai","ઓ":"oː","ઔ":"au","ા":"aː","િ":"i","ી":"iː","ુ":"u","ૂ":"uː","ે":"eː","ૈ":"ai","ો":"oː","ૌ":"au",
 "அ":"a","ஆ":"aː","இ":"i","ஈ":"iː","உ":"u","ஊ":"uː","எ":"e","ஏ":"eː","ஐ":"ai","ஒ":"o","ஓ":"oː","ஔ":"au","ா":"aː","ி":"i","ீ":"iː","ு":"u","ூ":"uː","ெ":"e","ே":"eː","ை":"ai","ொ":"o","ோ":"oː","ௌ":"au",
 "అ":"a","ఆ":"aː","ఇ":"i","ఈ":"iː","ఉ":"u","ఊ":"uː","ఎ":"e","ఏ":"eː","ఐ":"ai","ఒ":"o","ఓ":"oː","ఔ":"au","ా":"aː","ి":"i","ీ":"iː","ు":"u","ూ":"uː","ె":"e","ే":"eː","ై":"ai","ొ":"o","ో":"oː","ౌ":"au",
 "ಅ":"a","ಆ":"aː","ಇ":"i","ಈ":"iː","ಉ":"u","ಊ":"uː","ಎ":"e","ಏ":"eː","ಐ":"ai","ಒ":"o","ಓ":"oː","ಔ":"au","ಾ":"aː","ಿ":"i","ೀ":"iː","ು":"u","ೂ":"uː","ೆ":"e","ೇ":"eː","ೈ":"ai","ೊ":"o","ೋ":"oː","ೌ":"au",
 "അ":"a","ആ":"aː","ഇ":"i","ഈ":"iː","ഉ":"u","ഊ":"uː","എ":"e","ഏ":"eː","ഐ":"ai","ഒ":"o","ഓ":"oː","ഔ":"au","ാ":"aː","ി":"i","ീ":"iː","ു":"u","ൂ":"uː","െ":"e","േ":"eː","ൈ":"ai","ൊ":"o","ോ":"oː","ൌ":"au",
 "ଅ":"ɔ","ଆ":"a","ଇ":"i","ଈ":"iː","ଉ":"u","ଊ":"uː","ଏ":"e","ଐ":"oi","ଓ":"o","ଔ":"ou","ା":"a","ି":"i","ୀ":"iː","ୁ":"u","ୂ":"uː","େ":"e","ୈ":"oi","ୋ":"o","ୌ":"ou"}
_CONS = {"क":"k","ख":"kʰ","ग":"g","घ":"gʱ","ङ":"ŋ","च":"t͡ʃ","छ":"t͡ʃʰ","ज":"d͡ʒ","झ":"d͡ʒʱ","ञ":"ɲ","ट":"ʈ","ठ":"ʈʰ","ड":"ɖ","ढ":"ɖʱ","ण":"ɳ","त":"t̪","थ":"t̪ʰ","द":"d̪","ध":"d̪ʱ","न":"n","प":"p","फ":"pʰ","ब":"b","भ":"bʱ","म":"m","य":"j","र":"r","ल":"l","व":"ʋ","श":"ʃ","ष":"ʂ","स":"s","ह":"ɦ",
 "ਕ":"k","ਖ":"kʰ","ਗ":"g","ਘ":"gʱ","ਚ":"t͡ʃ","ਛ":"t͡ʃʰ","ਜ":"d͡ʒ","ਝ":"d͡ʒʱ","ਟ":"ʈ","ਠ":"ʈʰ","ਡ":"ɖ","ਢ":"ɖʱ","ਣ":"ɳ","ਤ":"t̪","ਥ":"t̪ʰ","ਦ":"d̪","ਧ":"d̪ʱ","ਨ":"n","ਪ":"p","ਫ":"pʰ","ਬ":"b","ਭ":"bʱ","ਮ":"m","ਯ":"j","ਰ":"r","ਲ":"l","ਵ":"ʋ","ਸ":"s","ਹ":"ɦ",
 "ক":"k","খ":"kʰ","গ":"g","ঘ":"gʱ","ঙ":"ŋ","চ":"t͡ʃ","ছ":"t͡ʃʰ","জ":"d͡ʒ","ঝ":"d͡ʒʱ","ট":"ʈ","ঠ":"ʈʰ","ড":"ɖ","ঢ":"ɖʱ","ণ":"ɳ","ত":"t̪","থ":"t̪ʰ","দ":"d̪","ধ":"d̪ʱ","ন":"n","প":"p","ফ":"pʰ","ব":"b","ভ":"bʱ","ম":"m","য":"d͡ʒ","র":"r","ল":"l","শ":"ʃ","ষ":"ʂ","স":"s","হ":"ɦ",
 "ક":"k","ખ":"kʰ","ગ":"g","ઘ":"gʱ","ચ":"t͡ʃ","છ":"t͡ʃʰ","જ":"d͡ʒ","ઝ":"d͡ʒʱ","ટ":"ʈ","ઠ":"ʈʰ","ડ":"ɖ","ઢ":"ɖʱ","ણ":"ɳ","ત":"t̪","થ":"t̪ʰ","દ":"d̪","ધ":"d̪ʱ","ન":"n","પ":"p","ફ":"pʰ","બ":"b","ભ":"bʱ","મ":"m","ય":"j","ર":"r","લ":"l","વ":"ʋ","શ":"ʃ","ષ":"ʂ","સ":"s","હ":"ɦ"}
# Dravidian and Odia consonants retain their native place/manner contrasts.
_CONS.update(dict(zip("கஙசஞடணதநபமயரலவழளறனஹ", "k ŋ t͡ʃ ɲ ʈ ɳ t̪ n p m j r l ʋ ɻ ɭ r n h".split())))
_CONS.update(dict(zip("కఖగఘంగచఛజఝఞటఠడఢణతథదధనపఫబభమయరలవశషసహళ", "k kʰ g gʱ ŋ t͡ʃ t͡ʃʰ d͡ʒ d͡ʒʱ ɲ ʈ ʈʰ ɖ ɖʱ ɳ t̪ t̪ʰ d̪ d̪ʱ n p pʰ b bʱ m j r l ʋ ʃ ʂ s ɦ ɭ".split())))
_CONS.update(dict(zip("ಕಖಗಘಙಚಛಜಝಞಟಠಡಢಣತಥದಧನಪಫಬಭಮಯರಲವಶಷಸಹಳ", "k kʰ g gʱ ŋ t͡ʃ t͡ʃʰ d͡ʒ d͡ʒʱ ɲ ʈ ʈʰ ɖ ɖʱ ɳ t̪ t̪ʰ d̪ d̪ʱ n p pʰ b bʱ m j r l ʋ ʃ ʂ s ɦ ɭ".split())))
_CONS.update(dict(zip("കഖഗഘങചഛജഝഞടഠഡഢണതഥദധനപഫബഭമയരലവശഷസഹളഴറ", "k kʰ g gʱ ŋ t͡ʃ t͡ʃʰ d͡ʒ d͡ʒʱ ɲ ʈ ʈʰ ɖ ɖʱ ɳ t̪ t̪ʰ d̪ d̪ʱ n p pʰ b bʱ m j r l ʋ ʃ ʂ s ɦ ɭ ɻ r".split())))
_CONS.update(dict(zip("କଖଗଘଙଚଛଜଝଞଟଠଡଢଣତଥଦଧନପଫବଭମଯରଲବଶଷସହଳ", "k kʰ g gʱ ŋ t͡ʃ t͡ʃʰ d͡ʒ d͡ʒʱ ɲ ʈ ʈʰ ɖ ɖʱ ɳ t̪ t̪ʰ d̪ d̪ʱ n p pʰ b bʱ m j r l ʋ ʃ ʂ s ɦ ɭ".split())))
_VIRAMA = set("઼्੍্્్್്୍")
_NASAL = set("ंঁંంಂംଂਂ")

def canonical_language(language: str | None) -> str:
    key = (language or "auto").strip().lower()
    if key not in _ALIASES: raise ValueError(f"Unsupported language '{language}'.")
    return _ALIASES[key]

def detect_language(text: str) -> str:
    chars = [ord(c) for c in text if c.isalpha()]
    scores = {l: sum(a <= c <= b for c in chars) for l, (a,b) in _BLOCKS.items()}
    winner, n = max(scores.items(), key=lambda x: x[1], default=("English", 0))
    if not n: return "English"
    # Shared scripts cannot distinguish Hindi/Marathi or Bengali/Assamese safely.
    return winner

def normalize_text(text: str, language: str | None = "auto") -> str:
    lang = canonical_language(language)
    text = unicodedata.normalize("NFC", text).translate(_DIGITS)
    text = re.sub(r"[।॥،؛!?.,:;]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if lang == "auto": detect_language(text)  # validates it is inspectable; do not transliterate unknown Roman text.
    return text

def _abugida(word: str, lang: str) -> list[str]:
    out: list[str] = []; pending = False
    for ch in word:
        if ch in _VIRAMA:
            if pending: pending = False
            continue
        if ch in _CONS:
            if pending: out.append("ə")
            out.append(_CONS[ch]); pending = True; continue
        if ch in _VOWELS:
            if pending: pending = False
            out.append(_VOWELS[ch]); continue
        if ch in _NASAL:
            if pending: out.append("ə"); pending = False
            out.append("ŋ" if lang in {"Bengali", "Assamese", "Odia"} else "̃"); continue
        if ch == "ः": out.append("h")
    if pending: out.append("ə")
    return out

def _urdu(word: str) -> list[str]:
    # Conservative Urdu/Persian inventory; short vowels are genuinely absent in
    # unvocalised Arabic orthography, so we do not invent them.
    table = {"ا":"aː","آ":"aː","ب":"b","پ":"p","ت":"t̪","ٹ":"ʈ","ث":"s","ج":"d͡ʒ","چ":"t͡ʃ","ح":"h","خ":"x","د":"d̪","ڈ":"ɖ","ذ":"z","ر":"r","ڑ":"ɽ","ز":"z","ژ":"ʒ","س":"s","ش":"ʃ","ص":"s","ض":"z","ط":"t̪","ظ":"z","ع":"ʔ","غ":"ɣ","ف":"f","ق":"q","ک":"k","گ":"g","ل":"l","م":"m","ن":"n","ں":"̃","و":"ʋ","ہ":"ɦ","ی":"j","ے":"eː","ئ":"j"}
    return [table[c] for c in word if c in table]

def syllabify(phones: Iterable[str]) -> list[list[str]]:
    """Maximal-onset broad syllables; useful for distributing a lyric over notes."""
    vowels = {"a","aː","ə","i","iː","u","uː","e","eː","o","oː","ɔ","ai","au","oi","ou","r̩"}
    result, current = [], []
    for p in phones:
        current.append(p)
        if p in vowels:
            result.append(current); current = []
    if current:
        (result[-1] if result else result).extend(current)
    return result or [["ə"]]

def phonemize_word(word: str, language: str | None = "auto") -> str:
    lang = canonical_language(language)
    if word in {"<SP>", "<AP>"}: return "<SP>"
    lang = detect_language(word) if lang == "auto" else lang
    if lang in {"English", "Mandarin", "Cantonese"}:
        raise ValueError("Use the legacy G2P frontend for English, Mandarin, or Cantonese.")
    phones = _urdu(word) if lang == "Urdu" else _abugida(word, lang)
    if not phones: raise ValueError(f"No native-script phonemes for {word!r} ({lang}); romanized input must be transliterated before use.")
    return SUPPORTED_LANGUAGES[lang] + "_" + "-".join(phones)

def phonemize_notes(words: Iterable[str], language: str | None = "auto") -> list[str]:
    return [phonemize_word(str(word), language) for word in words]
