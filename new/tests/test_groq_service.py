import pytest
from app.config import Settings
from app.services.groq_service import GroqLyricsService

def test_groq_requires_configuration():
    with pytest.raises(RuntimeError, match="Groq is not configured"):
        GroqLyricsService(Settings(groq_api_key=None, groq_model=None)).generate("Asha", "Hindi", "happy")
