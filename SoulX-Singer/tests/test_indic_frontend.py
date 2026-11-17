import unittest

from soulxsinger.text.indic import detect_language, phonemize_notes, syllabify
from soulxsinger.text.vocabulary import MULTILINGUAL_PHONEMES

SAMPLES = {
    "Hindi": "दिल", "Punjabi": "ਦਿਲ", "Haryanvi": "मन", "Bengali": "মন",
    "Tamil": "மனம்", "Telugu": "మనసు", "Kannada": "ಮನಸು", "Malayalam": "മനം",
    "Marathi": "मन", "Gujarati": "મન", "Urdu": "دل", "Odia": "ମନ", "Assamese": "মন",
}

class IndicFrontendTest(unittest.TestCase):
    def test_each_supported_language_has_native_phonemes(self):
        vocab = set(MULTILINGUAL_PHONEMES)
        for language, lyric in SAMPLES.items():
            with self.subTest(language=language):
                phones = phonemize_notes([lyric], language)[0].split("_")[1].split("-")
                self.assertTrue(phones)
                prefix = phonemize_notes([lyric], language)[0].split("_", 1)[0]
                self.assertTrue(all(f"{prefix}_{p}" in vocab for p in phones))

    def test_script_detection(self):
        self.assertEqual(detect_language("दिल"), "Hindi")
        self.assertEqual(detect_language("தமிழ்"), "Tamil")
        self.assertEqual(detect_language("دل"), "Urdu")

    def test_syllables_keep_all_phones(self):
        phones = ["k", "a", "n", "aː"]
        self.assertEqual([p for s in syllabify(phones) for p in s], phones)

if __name__ == "__main__":
    unittest.main()
