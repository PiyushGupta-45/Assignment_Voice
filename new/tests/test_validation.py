import pytest
from pydantic import ValidationError
from app.models.song_models import GenerateSongRequest
from app.utils.validation import validate_language, validate_lyrics

def test_empty_name_rejected():
    with pytest.raises(ValidationError): GenerateSongRequest(name="   ", language="Hindi", style="happy")
def test_unsupported_language_rejected():
    with pytest.raises(ValueError): validate_language("Klingon", {"Hindi", "English"})
def test_unsupported_style_rejected():
    with pytest.raises(ValidationError): GenerateSongRequest(name="Asha", language="Hindi", style="calm")
def test_exactly_four_lines():
    assert validate_lyrics(["one", "two", "three", "four"]) == ["one", "two", "three", "four"]
    with pytest.raises(ValueError): validate_lyrics(["one"] * 3)
