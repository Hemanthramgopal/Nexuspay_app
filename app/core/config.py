from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    OPENAI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENAI_MODEL: Optional[str] = None
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    MAX_SPEND_LIMIT: int = Field(default=15000, gt=0)
    MAX_DISCOUNT_PERCENT: int = Field(default=15, ge=0, le=100)

    @property
    def resolved_api_key(self) -> str:
        """Return the configured API key for OpenRouter/OpenAI compatibility."""
        return self.OPENROUTER_API_KEY
