# Specification: AP2 Permission Receipt & Intent Mandate (Unit 20)

## 1. Overview
To conclude our agentic commerce application with a robust, enterprise-grade finish, we are implementing Unit 20: the AP2 Permission Receipt (Intent Mandate). Before a final Razorpay checkout occurs (whether single-item or combo), the system generates a cryptographically-styled JSON "Intent Mandate" receipt. This receipt provides verifiable proof of human consent, detailing the agreed terms, timestamps, line items, and protocol standard (`ACP-v1.0`).

## 2. Target Files
- `app/services/mandate_service.py` (New file for generating cryptographic-style intent receipts)
- `app/models/schemas.py` (Add mandate request/response models)
- `app/api/routes.py` (Update checkout / order endpoints to generate and attach the mandate)
- `frontend/src/components/ChatInterface.jsx` (Display the Mandate/Receipt card prior to or during payment)
- `frontend/src/components/AuditTerminal.jsx` (Log the `MANDATE_GENERATED` security event)

## 3. Implementation Requirements

### 3.1. Mandate Service (`mandate_service.py`)
- Create a `MandateService` class.
- Implement a method `generate_mandate(order_id: str, items: list, total_amount: int, user_address_hash: Optional[str] = None) -> dict`.
- Generate a SHA-256 cryptographic signature based on the payload fields and a secret salt to simulate a secure, tamper-evident AP2 mandate token.
- Structure the JSON receipt to include:
  - `mandate_id`: `mandate_<uuid>`
  - `protocol`: `ACP-v1.0`
  - `timestamp`: ISO-8601 UTC string
  - `order_id`: Associated Razorpay order ID
  - `items`: Array of agreed product IDs and quantities
  - `total_amount_paise`: Integer total amount
  - `cryptographic_signature`: Hex-encoded SHA-256 token

### 3.2. Schemas & Routes Updates (`schemas.py` & `routes.py`)
- Update order-creation and combo-checkout responses to include an optional `intent_mandate` object.
- Ensure the audit logger logs a green/cyan `MANDATE_GENERATED` step.

### 3.3. Frontend Presentation (`ChatInterface.jsx` & `AuditTerminal.jsx`)
- Render an expandable "AP2 Intent Mandate / Permission Receipt" view inside the checkout card, showing the signature hash and authorized amount.
- Add a terminal trace for `MANDATE_GENERATED`.

## 4. Verification Steps
Before marking this task complete, you MUST:
1. Complete a successful single-item or combo negotiation.
2. Verify the backend response returns a structured `intent_mandate` containing a valid SHA-256 signature and `ACP-v1.0` metadata.
3. Verify the React UI displays the permission receipt details.
4. Mark Unit 20 complete and update the active task in `context/progress-tracker.md`.