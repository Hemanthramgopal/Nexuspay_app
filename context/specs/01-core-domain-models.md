# Spec: Unit 01 - Core Domain Models & Config

## 1. Objective
Establish the foundational data structures and environment configuration for the NexusPay Agentic Checkout gateway. Everything must be strictly typed using Pydantic v2. This unit sets up the contracts that the Gemini AI Agent, the Guardrail Interceptor, and the Razorpay Service will use to communicate.

## 2. Requirements & Dependencies
Modify/Create `requirements.txt` to include:
- `fastapi`
- `uvicorn`
- `pydantic>=2.0`
- `pydantic-settings` (for env var management)
- `google-genai` (The official Google Gen AI SDK for Python)
- `razorpay`

## 3. Configuration Management (`app/core/config.py`)
Create a `Settings` class inheriting from `pydantic_settings.BaseSettings`.
- **Variables:**
  - `GEMINI_API_KEY`: str
  - `RAZORPAY_KEY_ID`: str
  - `RAZORPAY_KEY_SECRET`: str
  - `MAX_SPEND_LIMIT`: int = 15000 (Razorpay safety bar limit)
  - `MAX_DISCOUNT_PERCENT`: int = 15 (Max allowed negotiation margin)

## 4. Domain Schemas (`app/models/domain.py`)
Create strict Pydantic v2 models. Use `Field` to enforce constraints natively.
- **Product:** `id` (str), `name` (str), `price` (int, strictly > 0), `stock` (int, >= 0), `category` (str).
- **OrderIntent:** Output by the AI Agent. `product_id` (str), `quantity` (int, > 0), `requested_discount_percent` (int, default 0, <= 100).
- **GuardrailResult:** The firewall output. `passed` (bool), `reason` (str, optional), `final_price` (int, optional).
- **AuditRecord:** `step` (str), `action` (str), `status` (str - "SUCCESS"|"FAILED"|"BLOCKED"), `details` (str), `timestamp` (datetime).

## 5. Razorpay Schemas (`app/models/razorpay_models.py`)
Create typed wrappers so we never pass raw dictionaries to the Razorpay SDK.
- **RazorpayOrderRequest:** `amount` (int, in paise), `currency` (str, default "INR"), `notes` (dict of strings).
- **RazorpayOrderResponse:** `id` (str), `entity` (str), `amount` (int), `status` (str).

## 6. Acceptance Criteria
- `pip install -r requirements.txt` succeeds.
- All Pydantic models instantiate correctly and reject invalid data (e.g., negative prices) via typechecks.
- Code passes standard Pyright/Ruff linting.