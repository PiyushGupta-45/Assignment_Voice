from app.config import Settings
from app.services.cache_service import cache_key

def test_cache_key_consistent_and_sensitive_to_inputs():
    settings = Settings()
    first = cache_key(" Rahul ", "Hindi", "happy", settings)
    assert first == cache_key("rahul", "Hindi", "happy", settings)
    assert first != cache_key("Rahul", "English", "happy", settings)
    assert first != cache_key("Rahul", "Hindi", "birthday", settings)
