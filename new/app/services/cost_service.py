import logging
from app.config import Settings

log = logging.getLogger(__name__)

def log_estimated_cost(settings: Settings, chars: int, prompt_tokens: int | None, completion_tokens: int | None) -> None:
    groq = ((prompt_tokens or 0) + (completion_tokens or 0)) / 1_000_000 * settings.groq_cost_per_million_tokens_inr
    sarvam = chars / 1000 * settings.sarvam_cost_per_1000_chars_inr
    log.info("estimated_ai_inference_cost_inr=%.4f groq_tokens=%s sarvam_chars=%d", groq + sarvam, (prompt_tokens or 0)+(completion_tokens or 0), chars)
