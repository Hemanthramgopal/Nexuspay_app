# Specification: Razorpay Checkout Execution & Order Creation (Unit 16)

## 1. Overview
When a negotiation reaches an agreement (`agreed: True`), the system must transition from the haggling state to the checkout state. This unit connects the negotiated final price to the Razorpay payment client (built in Unit 03) to generate a genuine Test Mode `order_id`, emit a final audit trace for order creation, and surface an interactive payment link or checkout action in the React frontend.

## 2. Target Files
- `app/services/payment_service.py` (or existing Razorpay client service)
- `app/api/routes.py` (add/update checkout execution endpoint)
- `app/models/schemas.py` (add checkout response and order schemas)
- `frontend/src/components/ChatInterface.jsx` (render the payment card / Razorpay button)
- `frontend/src/components/AuditTerminal.jsx` (display the `ORDER_CREATED` gated audit trace)

## 3. Implementation Requirements

### 3.1. Order Creation Endpoint & Logic
- **Endpoint**: `POST /api/v1/create-order` (or integrate directly into the successful `semantic-negotiation` payload when `agreed: True`).
- **Request Payload**:
  ```json
  {
    "product_id": "mechanical_keyboard_87keys",
    "final_price": 3600,
    "currency": "INR"
  }


Backend Guardrail Enforcement:

Re-verify against catalog.db that final_price >= min_price before executing any payment call (ensuring no client-side price tampering).

Use the Razorpay client (Test Mode API key/secret or test service) to generate a valid order_id with amount in paise (final_price * 100).

Response Structure:

JSON
{
  "success": true,
  "order_id": "order_xyz12345",
  "amount": 3600,
  "currency": "INR",
  "product_name": "Mechanical Keyboard 87 Keys",
  "payment_url": "[https://rzp.io/i/mock_or_test_link](https://rzp.io/i/mock_or_test_link)",
  "audit_record": {
    "step": "ORDER_CREATED",
    "status": "SUCCESS",
    "details": "Razorpay order created for ₹3,600 (Order ID: order_xyz12345)"
  }
}
3.2. Frontend React Integration
Interactive Action in ChatInterface.jsx:

When a message response contains agreed: true (or an explicit order_id / payment_url), render an actionable "Complete Checkout via Razorpay" card below the seller message.

Display the finalized price badge, item summary, and a branded Razorpay blue action button (bg-blue-600 hover:bg-blue-700).

Audit Terminal Update:

Dynamically push the ORDER_CREATED audit block into the AuditTerminal with emerald styling, explicitly demonstrating the transaction gating and final money action.

4. Verification Steps
Before marking this task complete, you MUST:

Trigger a successful negotiation (e.g., offer ₹4,000 for the keyboard or accept an agent's counter-offer).

Verify the backend creates an order with a valid order_id and correct amount in paise (400000 paise for ₹4,000).

Verify the React chat window renders the payment card with the checkout action.

Verify the Audit Terminal shows the green ORDER_CREATED step with the order ID.