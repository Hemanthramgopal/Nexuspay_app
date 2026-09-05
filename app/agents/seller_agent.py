import json
import sqlite3
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from app.core.config import Settings
from app.services.llm_service import LLMResponse, LLMService


settings = Settings()


class NegotiationResult(BaseModel):
    """Structured output for the seller negotiation flow."""

    model_config = ConfigDict(strict=True)

    agreed: bool
    final_price: int
    message_to_buyer: str


class SellerAgent:
    """Negotiate with a buyer while enforcing the catalog minimum price floor."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.llm_service = LLMService(settings)
        self.last_benchmark: LLMResponse | None = None

    def _fallback_rejection(self, offered_price: int, min_price: int) -> NegotiationResult:
        """Return a deterministic rejection when the LLM response is absent or invalid."""
        return NegotiationResult(
            agreed=False,
            final_price=min_price,
            message_to_buyer=(
                f"I appreciate the offer, but I cannot accept ₹{offered_price}. "
                f"I can offer this product at ₹{min_price}."
            ),
        )

    def _extract_model_content(self, response: object) -> str | None:
        """Safely extract the model text from OpenAI-style responses."""
        try:
            choices = getattr(response, "choices", None) or []
            if not choices:
                return None

            first_choice = choices[0]
            message = getattr(first_choice, "message", None)
            if message is None:
                return None

            content = getattr(message, "content", None)
            if content is None:
                return None

            if isinstance(content, str):
                return content.strip() or None

            return str(content).strip() or None
        except Exception:
            return None

    def _db_path(self) -> Path:
        """Resolve the local catalog database path relative to the project root."""
        return Path(__file__).resolve().parents[2] / "catalog.db"

    def get_product_constraints(self, product_id: str) -> tuple[int, int, int]:
        """Return the base price, min price, and stock for a product from SQLite."""
        conn = sqlite3.connect(self._db_path())
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT base_price, min_price, stock FROM products WHERE LOWER(id) = LOWER(?)",
            (product_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            raise ValueError(f"Product not found in catalog database: {product_id}")

        return int(row["base_price"]), int(row["min_price"]), int(row["stock"])

    def negotiate(
        self,
        product_id: str,
        offered_price: int,
        buyer_prompt: str | None = None,
        chat_history: list[dict[str, str]] | None = None,
    ) -> NegotiationResult:
        """Compatibility wrapper for the seller negotiation contract used by the API layer."""
        return self.negotiate_price(product_id, offered_price, buyer_prompt, chat_history)

    def negotiate_price(
        self,
        product_id: str,
        offered_price: int,
        buyer_prompt: str | None = None,
        chat_history: list[dict[str, str]] | None = None,
    ) -> NegotiationResult:
        """Negotiate a buyer offer while enforcing the database price floor."""
        _, min_price, _ = self.get_product_constraints(product_id)

        system_instruction = (
            "You are the NexusPay seller agent acting as a professional, persuasive merchant. "
            "Keep the internal floor confidential during normal negotiation, but when the buyer's offer is below it, "
            "you must disclose the exact floor as the required counter-offer. Do not mention the base price. "
            "Keep your pricing strategy discreet and professional. "
            "If the buyer's offer is greater than or equal to product.min_price (e.g. ₹3,500), you MUST accept the deal. "
            "Return JSON with 'agreed': true, 'final_price': <offered_price>, and a polite confirmation message. "
            "If the buyer offer is below what you can accept, negotiate politely and produce a counter-offer that keeps the conversation credible and respectful. "
            "Your response must be a JSON object with keys: agreed, final_price, message_to_buyer. "
            "Set agreed to true only when the final_price is at least the minimum allowed price. "
            f"If the buyer offer is below the minimum floor, do not agree to it. The user offered ₹{offered_price}, "
            f"which is below our floor. You must politely reject this and counter-offer exactly ₹{min_price}. "
            "Mention the counter-offer naturally in message_to_buyer."
        )

        messages = [
            {"role": "system", "content": system_instruction},
        ]
        messages.extend(chat_history or [])
        messages.append(
            {
                "role": "user",
                "content": (
                    f"The buyer's request was: {buyer_prompt or f'Offer ₹{offered_price}.'} "
                    f"The parsed offer is ₹{offered_price} for product_id {product_id}. "
                    "Respond with a negotiation result that follows the minimum price floor and keeps the final price realistic."
                ),
            }
        )

        try:
            self.last_benchmark = self.llm_service.complete_json(
                messages=messages,
            )
        except Exception:
            return self._fallback_rejection(offered_price, min_price)

        content = self.last_benchmark["content"] if self.last_benchmark else None
        if content is None:
            return self._fallback_rejection(offered_price, min_price)

        try:
            data = json.loads(content)
            result = NegotiationResult.model_validate(data)
        except Exception:
            return self._fallback_rejection(offered_price, min_price)

        if offered_price == 0:
            result.agreed = False
            result.final_price = 0
            result.message_to_buyer = (
                f"I can help you negotiate the {product_id.replace('_', ' ')}, but what price would you like to offer?"
            )
            return result

        if offered_price >= min_price:
            result.agreed = True
            result.final_price = offered_price
            result.message_to_buyer = (
                f"Accepted. Thank you for your offer, I can confirm the price at ₹{offered_price}."
            )
            return result

        if offered_price < min_price:
            result.agreed = False
            result.final_price = min_price

        return result
