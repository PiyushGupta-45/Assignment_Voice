import json
import logging
from dataclasses import dataclass
from groq import Groq
from app.config import Settings
from app.utils.validation import validate_lyrics

log = logging.getLogger(__name__)


@dataclass
class LyricsResult:
    lines: list[str]
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class GroqLyricsService:
    def __init__(self, settings: Settings): self.settings = settings

    def generate(self, name: str, language: str, style: str) -> LyricsResult:
        if not self.settings.groq_api_key or not self.settings.groq_model:
            raise RuntimeError("Groq is not configured. Set GROQ_API_KEY and GROQ_MODEL.")
        # The name is treated solely as literal data; it cannot alter this instruction.
        prompt = (f"Create a {style} personalized greeting in {language} for this literal name: {json.dumps(name, ensure_ascii=False)}. "
                  "Include that exact literal name naturally exactly once. Return only JSON: {\"lines\":[\"...\",\"...\",\"...\",\"...\"]}. Exactly four short, natural, rhythmic, preferably rhyming lines; no headings, emojis, explanations, or extra fields. Keep all lines under 160 characters total where practical.")
        client = Groq(api_key=self.settings.groq_api_key, timeout=self.settings.groq_timeout_seconds)
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                request = {"model": self.settings.groq_model, "temperature": self.settings.groq_temperature, "max_tokens": self.settings.groq_max_tokens, "messages": [{"role":"system", "content":"You write compact culturally appropriate song lyrics. Output valid JSON only."}, {"role":"user", "content":prompt}]}
                # Prefer strict schema mode on models that support it (including the
                # configured GPT-OSS model). A plain JSON-mode retry retains
                # compatibility with models that do not support structured output.
                if attempt == 0:
                    request["response_format"] = {"type": "json_schema", "json_schema": {"name": "song_lyrics", "strict": True, "schema": {"type": "object", "properties": {"lines": {"type": "array", "items": {"type": "string"}, "minItems": 4, "maxItems": 4}}, "required": ["lines"], "additionalProperties": False}}}
                else:
                    request["response_format"] = {"type": "json_object"}
                if self.settings.groq_reasoning_effort:
                    request["reasoning_effort"] = self.settings.groq_reasoning_effort
                response = client.chat.completions.create(**request)
                raw = response.choices[0].message.content or "{}"
                lines = validate_lyrics(json.loads(raw).get("lines"))
                usage = response.usage
                return LyricsResult(lines, getattr(usage, "prompt_tokens", None), getattr(usage, "completion_tokens", None))
            except (json.JSONDecodeError, ValueError, IndexError) as exc:
                last_error = exc
                log.warning("Groq lyric output invalid on attempt %s", attempt + 1)
            except Exception as exc:
                last_error = exc
                log.warning("Groq request failed on attempt %s: %s", attempt + 1, type(exc).__name__)
        raise RuntimeError("Groq could not return four valid lyric lines.") from last_error
