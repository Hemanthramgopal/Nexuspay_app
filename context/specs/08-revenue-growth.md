# Spec: Unit 08 - Cart Upgrades & Cross-Selling

## 1. Objective
Upgrade the system to support multi-item carts, allowing the agent to dynamically cross-sell accessories (e.g., adding a charger when a user buys a smartphone) to increase the merchant's Average Order Value (AOV).

## 2. Requirements & Files
- Modify `app/models/domain.py`.
- Modify `app/agents/agent.py`.
- Modify `app/services/guardrails.py`.
- Modify `app/api/routes.py`.

## 3. Implementation Details
- **Upgrade `OrderIntent`:** 
  - Change `product_id: str` and `quantity: int` to a list of items: `items: list[CartItem]`.
  - Create a new `CartItem` Pydantic model with `product_id: str` and `quantity: int`.
- **Update the Agent (`agent.py`):**
  - Modify the `system_instruction`. Instruct the agent: "If the user buys a primary device (like a laptop or smartphone), you must proactively search for a relevant, low-cost accessory (like a mouse or charger) and add it to the order intent to grow merchant revenue."
- **Update the Firewall (`guardrails.py` & `routes.py`):**
  - Adjust the logic to iterate through the `items` list, fetch each product via `CatalogService`, calculate the combined `gross_price` (summing `quantity * price` for all items), apply the `requested_discount_percent`, and ensure the final total is still `<= MAX_SPEND_LIMIT`.

## 4. Acceptance Criteria
- When a user asks to "Buy a smartphone," the final `CheckoutResponse` shows an intent containing *both* the smartphone and a related accessory fetched from DummyJSON.
- The guardrails successfully calculate the total cart value and block it if the combined price exceeds ₹15,000.