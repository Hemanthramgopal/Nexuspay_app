import json

from app.core.config import Settings
from app.core.exceptions import AgentExecutionError, ProductNotFoundError
from app.models.domain import OrderIntent
from app.services.catalog_service import CatalogService
from app.services.llm_service import LLMResponse, LLMService


settings = Settings()


class BuyerAgent:
    """Translate natural-language purchase requests into order intents."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self.llm_service = LLMService(settings)
        self.last_benchmark: LLMResponse | None = None

    def _fallback_intent(self, user_input: str) -> OrderIntent:
        """Deterministically map common prompts to catalog-approved products."""
        normalized = (user_input or "").lower()
        catalog = CatalogService()

        product_map = {
            "mechanical keyboard": "mechanical_keyboard_87keys",
            "keyboard": "mechanical_keyboard_87keys",
            "gaming laptop": "gaming_laptop",
            "premium monitor": "premium_monitor",
            "monitor": "premium_monitor",
            "laptop": "laptop",
            "notebook": "laptop",
            "smartphone": "smartphone",
            "mobile phone": "smartphone",
            "phone": "smartphone",
            "gaming console": "gaming_console",
            "console": "gaming_console",
            "smartwatch": "smartwatch",
            "tablet": "tablet",
            "speaker": "bluetooth_speaker",
            "headphones": "wireless_headphones",
        }

        chosen_id = None
        for phrase, product_id in product_map.items():
            if phrase in normalized:
                chosen_id = product_id
                break

        if chosen_id is None:
            for product in catalog._products:
                if product.name.lower() in normalized or product.category.lower() in normalized:
                    chosen_id = product.id
                    break

        if chosen_id is None:
            raise AgentExecutionError("No supported product could be inferred from the prompt.")

        discharge = False
        if chosen_id in {"smartphone", "laptop", "premium_monitor"}:
            accessory_id = "usb_c_charger"
            if "charger" in normalized or "accessory" in normalized:
                items = [
                    {"product_id": chosen_id, "quantity": 1},
                    {"product_id": accessory_id, "quantity": 1},
                ]
                discharge = True
        if not discharge:
            items = [{"product_id": chosen_id, "quantity": 1}]

        percent = 0
        for token in normalized.split():
            if "%" in token:
                try:
                    percent = int(token.strip('%'))
                    break
                except ValueError:
                    continue

        return OrderIntent.model_validate(
            {"items": items, "requested_discount_percent": percent}
        )

    def process_user_intent(self, user_input: str) -> OrderIntent:
        """Generate and validate a structured order intent from user input."""
        system_instruction = (
            "You are the NexusPay Buyer Agent. Return a JSON object only, matching this exact structure:\n"
            "{\"items\": [{\"product_id\": \"<name_or_id>\", \"quantity\": <int>}],\n"
            "\"requested_discount_percent\": <int>}\n\n"
            "CRITICAL RULES:\n"
            "1. Extract the primary product requested and map it accurately.\n"
            "2. Use ONLY these catalog-safe product IDs: smartphone, laptop, gaming_laptop, mechanical_keyboard_87keys, premium_monitor, ergonomic_mouse, usb_c_charger, wireless_headphones.\n"
            "3. CROSS-SELL: When a primary device (like smartphone, laptop, or monitor) is requested, ALWAYS include a low-cost accessory (like usb_c_charger or ergonomic_mouse) in the items list alongside the primary item.\n"
            "4. Keep requested_discount_percent an integer between 0 and 100."
        )
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_input},
        ]

        try:
            self.last_benchmark = self.llm_service.complete_json(
                messages=messages,
            )
            content = self.last_benchmark["content"]
            if not content:
                return self._fallback_intent(user_input)

            data = json.loads(content)
            intent = OrderIntent.model_validate(data)
            for item in intent.items:
                catalog = CatalogService()
                catalog.get_product(item.product_id)
            return intent
        except (AgentExecutionError, ProductNotFoundError, ValueError, TypeError):
            return self._fallback_intent(user_input)
        except Exception as error:
            return self._fallback_intent(user_input)
