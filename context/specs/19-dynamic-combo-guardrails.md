# Specification: Dynamic Combo Guardrails (Unit 19)

## 1. Overview
The Upsell Worker Agent successfully pitches a recommended add-on, and the UI displays an "Add to Order" action. We must now implement a secure combo-checkout flow. This unit introduces a new endpoint that calculates the combined total of the negotiated primary item and the upsell item, enforces a dynamic guardrail (combo total must be >= combined min_prices), and generates a new Razorpay `order_id` for the multi-item cart.

## 2. Target Files
- `app/api/routes.py` (Add new combo checkout endpoint)
- `app/models/schemas.py` (Add combo request/response schemas)
- `frontend/src/components/ChatInterface.jsx` (Wire the "Add to Order" button)
- `frontend/src/components/AuditTerminal.jsx` (Log the combo validation and updated order)

## 3. Implementation Requirements

### 3.1. Schemas (`schemas.py`)
Add models to handle the combo checkout request:
```python
class ComboCheckoutRequest(BaseModel):
    primary_product_id: str
    primary_agreed_price: int
    upsell_product_id: str

class ComboCheckoutResponse(BaseModel):
    success: bool
    order_id: str
    total_amount: int
    currency: str
    message: str
3.2. Combo Checkout Endpoint (routes.py)
Create POST /api/v1/checkout-combo.

Dynamic Guardrail Logic:

Fetch both primary_product_id and upsell_product_id from catalog.db.

Calculate combo_min_price = primary_item.min_price + upsell_item.min_price.

Calculate proposed_total = primary_agreed_price + upsell_item.base_price.

Strict Enforcement: If proposed_total < combo_min_price, reject the transaction (HTTP 400).

If valid, use the Razorpay client to generate a new order_id for proposed_total * 100 (paise).

Add an audit step: COMBO_GUARDRAIL_PASSED followed by ORDER_UPDATED.

3.3. Frontend Integration (ChatInterface.jsx & AuditTerminal.jsx)
Wire the "Add to Order" button in the checkout card to call POST /api/v1/checkout-combo with the agreed price and both item IDs.

On success, update the checkout card UI to reflect the new total_amount and the new order_id.

Update the Audit Terminal to show a blue COMBO_GUARDRAIL_PASSED log and a green ORDER_UPDATED log.

4. Verification Steps
Before marking this task complete, you MUST:

Complete a negotiation for the keyboard at ₹4,000 (which prompts the ₹2,000 mouse upsell).

Click "Add to Order" (or simulate the POST request).

Verify the backend successfully validates the combo (₹4,000 + ₹2,000 = ₹6,000) against the floor prices, generating a new Razorpay order for 600,000 paise.

Verify the React UI updates the payment card total to ₹6,000 and logs the guardrail passage in the terminal.