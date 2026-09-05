"""Worker agent that creates concise catalog-driven cross-sell pitches."""

import json
import re

from app.core.config import Settings
from app.services.llm_service import LLMService


settings = Settings()


class UpsellAgent:
    """Generate a one-sentence cross-sell pitch after a successful agreement."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.llm_service = LLMService(settings)

    def generate_pitch(
        self,
        primary_item_name: str,
        addon_item_name: str,
        addon_price: int,
    ) -> str:
        """Generate one short cross-sell sentence, with a safe deterministic fallback."""
        system_instruction = (
            "You are an expert e-commerce cross-sell agent. The buyer just agreed to buy "
            f"{primary_item_name}. Pitch them the {addon_item_name} for ₹{addon_price}. "
            "Keep it to exactly one short sentence. Do not mention discounts unless explicitly told."
        )
        fallback = (
            f"Complete your {primary_item_name} setup with the {addon_item_name} for ₹{addon_price:,}."
        )

        try:
            response = self.llm_service.complete_json(
                messages=[
                    {
                        "role": "system",
                        "content": f'{system_instruction} Return only JSON: {{"pitch": "..."}}',
                    }
                ],
            )
            content = json.loads(response["content"]).get("pitch")
            if not isinstance(content, str) or not content.strip():
                return fallback
        except Exception:
            return fallback

        sentence = re.split(r"(?<=[.!?])\s+", content.strip())[0].strip()
        if not sentence:
            return fallback
        return sentence if sentence.endswith((".", "!", "?")) else f"{sentence}."
