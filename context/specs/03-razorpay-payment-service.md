# Spec: Unit 03 - Razorpay Payment Service

## 1. Objective
Integrate the official `razorpay` Python SDK to create sandbox orders. The service must enforce strict defensive practices: it will only execute when provided a valid `OrderIntent`, `Product`, and an approved `GuardrailResult`. It will also emit an `AuditRecord` documenting the transaction creation.

## 2. Requirements & Files
- `app/services/payment_service.py`
- Modify `app/core/exceptions.py` to add `PaymentServiceError`

## 3. Exceptions (`app/core/exceptions.py`)
Add a domain-specific exception:
- `PaymentServiceError(Exception)`: Raised when the Razorpay client initialization fails or the API call returns an error.

## 4. Payment Service Implementation (`app/services/payment_service.py`)
Create a `PaymentService` class.

- **Initialization (`__init__`):**
  - Accept optional `key_id: str | None` and `key_secret: str | None`.
  - If not provided, load them from `app.core.config.settings`.
  - Initialize the `razorpay.Client(auth=(key_id, key_secret))`.

- **Method: `create_payment_order(intent: OrderIntent, product: Product, guardrail_result: GuardrailResult) -> tuple[RazorpayOrderResponse, AuditRecord]`**
  - **Prerequisite Check:** If `guardrail_result.passed` is `False` or `guardrail_result.final_price` is `None`, raise `PaymentServiceError("Cannot initiate payment on unverified or failed order intent.")`.
  - **Amount Calculation:** Convert `guardrail_result.final_price` into **paise** (`amount_in_paise = guardrail_result.final_price * 100`).
  - **Payload Construction:** Build a `RazorpayOrderRequest` with:
    - `amount`: `amount_in_paise`
    - `currency`: `"INR"`
    - `notes`: `{"product_id": product.id, "quantity": str(intent.quantity), "discount": str(intent.requested_discount_percent)}`
  - **SDK Invocation:** Call `self.client.order.create(data=request.model_dump())`.
  - **Error Handling:** Wrap the SDK call in a `try...except Exception as e` block. On failure, raise `PaymentServiceError(f"Razorpay order creation failed: {str(e)}")`.
  - **Audit Logging:** Upon success, construct and return an `AuditRecord`:
    - `step`: `"PAYMENT_GATEWAY"`
    - `action`: `"CREATE_ORDER"`
    - `status`: `"SUCCESS"`
    - `details`: `f"Created Razorpay order {response_data['id']} for amount ₹{guardrail_result.final_price}"`
    - `timestamp`: Current UTC datetime.
  - Return a typed `RazorpayOrderResponse` along with the `AuditRecord`.

## 5. Acceptance Criteria
- `PaymentService` can be initialized with mock test credentials.
- Attempting to pass a `GuardrailResult(passed=False)` immediately raises `PaymentServiceError`.
- Valid inputs generate a typed `RazorpayOrderResponse` and an `AuditRecord`.
- For offline/mock validation (when active network test keys are unavailable), SDK calls can be mocked using standard `unittest.mock` to verify payload conversion and paise calculation.