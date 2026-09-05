# Spec: Unit 05 - FastAPI Endpoints & Failure Recovery

## 1. Objective
Expose the NexusPay agentic pipeline via a REST API. The endpoint must orchestrate the complete flow: Intent Parsing -> Catalog Lookup -> Guardrail Verification -> Payment Execution. Critically, it must demonstrate "Graceful Failure" by catching guardrail violations and returning a structured, auditable response instead of crashing with a 500 Server Error.

## 2. Requirements & Files
- `app/api/__init__.py`
- `app/api/routes.py`
- `app/main.py`

## 3. API Schemas (`app/api/routes.py`)
Define Pydantic models for the HTTP request and response:
- **CheckoutRequest:** `prompt` (str) - e.g., "Buy the mechanical keyboard and ask for a 10% discount."
- **CheckoutResponse:** 
  - `success` (bool)
  - `intent` (OrderIntent | None)
  - `guardrail_result` (GuardrailResult | None)
  - `payment_order` (RazorpayOrderResponse | None)
  - `audit` (AuditRecord)

## 4. Endpoint Logic (`app/api/routes.py`)
Create a FastAPI `APIRouter`.
- **POST `/api/v1/agentic-checkout`**
  - **Step 1:** Initialize `BuyerAgent()`, `CatalogService()`, and `PaymentService()`.
  - **Step 2 (Agent):** Call `agent.process_user_intent(request.prompt)` to get the `OrderIntent`.
  - **Step 3 (Catalog):** Fetch the `Product` using `catalog.get_product(intent.product_id)`.
  - **Step 4 (Guardrail):** Evaluate `verify_order_intent(intent, product)`.
  - **Step 5 (Payment or Graceful Failure):**
    - If `guardrail_result.passed` is `True`: Call `payment_service.create_payment_order(...)`. Return a `CheckoutResponse` with `success=True` and the generated order/audit data.
    - If `guardrail_result.passed` is `False`: Do NOT throw an HTTP 500. Instead, construct a localized `AuditRecord` (status="BLOCKED", details=guardrail_result.reason). Return a `CheckoutResponse` with `success=False` and the blocked audit trace.
  - **Exception Handling:** Catch `AgentExecutionError` and `CatalogError`, returning HTTP 400 with a clear error message.

## 5. Application Initialization (`app/main.py`)
- Initialize `FastAPI(title="NexusPay Agentic Gateway")`.
- Add `CORSMiddleware` (allow origins `["*"]`, methods `["*"]`, headers `["*"]`) so the frontend UI can connect.
- Include the router from `app.api.routes`.

## 6. Acceptance Criteria
- `uvicorn app.main:app --reload` starts the server without errors.
- A request for a ₹4,000 keyboard returns `success: true` with a Razorpay Order ID.
- A request for the ₹18,000 premium monitor gracefully returns `success: false` with the Guardrail rejection reason in the audit log, proving the Razorpay safety constraints are active.