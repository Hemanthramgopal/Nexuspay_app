"""OpenAI-compatible multi-provider LLM routing with cooldown recovery."""

import json
import time
from typing import TypedDict

from openai import OpenAI, RateLimitError

from app.core.config import Settings


class LLMResponse(TypedDict):
    """Sanitized model response and routing benchmark metadata."""

    content: str
    provider_used: str
    model_used: str
    latency_seconds: float


class ProviderState(TypedDict):
    """Configured provider state kept by the in-memory circuit breaker."""

    name: str
    model: str
    base_url: str
    api_key: str
    cooldown_until: float


class LLMService:
    """Route JSON completions through a priority pool with automatic cooldowns."""

    COOLDOWN_SECONDS = 60.0
    _providers: list[ProviderState] | None = None

    def __init__(self, settings: Settings | None = None) -> None:
        resolved_settings = settings or Settings()
        if LLMService._providers is not None:
            self.providers = LLMService._providers
            return

        self.providers = [
            {
                "name": "OpenRouter/Nemotron",
                "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": resolved_settings.OPENROUTER_API_KEY,
                "cooldown_until": 0.0,
            },
            {
                "name": "Groq",
                "model": "llama-3.1-8b-instant",
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": resolved_settings.GROQ_API_KEY,
                "cooldown_until": 0.0,
            },
            {
                "name": "Gemini",
                "model": "gemini-3.5-flash-lite",
                "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                "api_key": resolved_settings.GEMINI_API_KEY,
                "cooldown_until": 0.0,
            },
            {
                "name": "OpenRouter/GLM",
                "model": "z-ai/glm-5.2:free",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": resolved_settings.OPENROUTER_API_KEY,
                "cooldown_until": 0.0,
            },
        ]
        LLMService._providers = self.providers

    @staticmethod
    def _sanitize_content(content: str) -> str:
        """Remove markdown fences while preserving the JSON payload."""
        sanitized = content.strip()
        if sanitized.startswith("```"):
            lines = sanitized.splitlines()
            if lines and lines[0].strip().lower() in {"```", "```json"}:
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            sanitized = "\n".join(lines).strip()
        return sanitized

    @staticmethod
    def _is_retryable_error(error: Exception) -> bool:
        """Identify rate limits and transient upstream HTTP failures."""
        if isinstance(error, RateLimitError):
            return True
        status_code = getattr(error, "status_code", None)
        return isinstance(status_code, int) and (status_code == 429 or status_code >= 500)

    def _fallback(self) -> str:
        """Return a schema-compatible counter-offer when all providers fail."""
        return json.dumps(
            {
                "agreed": False,
                "final_price": 0,
                "message_to_buyer": "I cannot complete the negotiation right now. Please try again shortly.",
            }
        )

    def complete_json(self, messages: list[dict[str, str]]) -> LLMResponse:
        """Request a JSON completion, failing over through the provider priority pool."""
        started_at = time.perf_counter()
        last_provider = "fallback"
        last_model = "deterministic-counter-offer"

        for provider in self.providers:
            if time.time() < provider["cooldown_until"]:
                continue
            last_provider = provider["name"]
            last_model = provider["model"]
            if not provider["api_key"]:
                continue

            try:
                client = OpenAI(base_url=provider["base_url"], api_key=provider["api_key"])
                response = client.chat.completions.create(
                    model=provider["model"],
                    messages=messages,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content or self._fallback()
                parsed_content = self._sanitize_content(content)
                json.loads(parsed_content)
                return {
                    "content": parsed_content,
                    "provider_used": provider["name"],
                    "model_used": provider["model"],
                    "latency_seconds": round(time.perf_counter() - started_at, 2),
                }
            except Exception as error:
                if self._is_retryable_error(error):
                    provider["cooldown_until"] = time.time() + self.COOLDOWN_SECONDS
                continue

        return {
            "content": self._fallback(),
            "provider_used": last_provider,
            "model_used": last_model,
            "latency_seconds": round(time.perf_counter() - started_at, 2),
        }
