# Spec: Unit 02 - Mock Catalog & Guardrail Firewall

## 1. Objective
Build the simulated merchant environment and the deterministic safety layer. The Catalog Service will provide machine-readable inventory to the agent. The Guardrail module will act as a strict mandate enforcer, blocking any `OrderIntent` that breaches stock, discount bounds, or the global spend ceiling (₹15,000).

## 2. Requirements & Files
- `app/core/exceptions.py`
- `app/services/catalog_service.py`
- `app/core/guardrails.py`

## 3. Exceptions (`app/core/exceptions.py`)
Define custom Python exceptions to handle domain errors gracefully:
- `CatalogError` (Base class)
- `ProductNotFoundError`
- `GuardrailViolationError`

## 4. Catalog Service (`app/services/catalog_service.py`)
Create a `CatalogService` class. 
- Initialize an internal list of `Product` models (mock data). Include at least 3 items (e.g., a mechanical keyboard for ₹4000, an ergonomic mouse for ₹2000, and a premium monitor for ₹18000 to test the spend limit).
- **Methods:**
  - `get_product(product_id: str) -> Product`: Raises `ProductNotFoundError` if missing.
  - `search_products(query: str) -> list[Product]`: Returns a list of products matching the query string (simple substring match on name/category is sufficient).

## 5. Guardrail Firewall (`app/core/guardrails.py`)
Create a pure function: `verify_order_intent(intent: OrderIntent, product: Product) -> GuardrailResult`.
- **Validation Rules:**
  1. **Stock Check:** `intent.quantity` must be $\le$ `product.stock`.
  2. **Discount Check:** `intent.requested_discount_percent` must be $\le$ `settings.MAX_DISCOUNT_PERCENT`.
  3. **Spend Limit Check:** Calculate `final_price = (product.price * intent.quantity) * (1 - (intent.requested_discount_percent / 100))`. The `final_price` must be $\le$ `settings.MAX_SPEND_LIMIT`.
- **Return Behavior:**
  - If all checks pass, return `GuardrailResult(passed=True, final_price=final_price)`.
  - If any check fails, return `GuardrailResult(passed=False, reason="...specific failure reason...")`. Do not throw an exception here; the result object allows the agent to read the failure and gracefully recover.

## 6. Acceptance Criteria
- `CatalogService` correctly returns populated Pydantic `Product` models.
- `verify_order_intent` correctly calculates the discounted price and explicitly rejects intents that breach the 15% discount limit or the ₹15,000 spend limit.
- Code uses proper type hints and depends entirely on the Unit 01 Pydantic models.