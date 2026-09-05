# Build Plan: NexusPay v1 (Steel Thread)

## Objective
Build a deterministic single-agent checkout engine using FastAPI, Gemini function calling, deterministic guardrails, and Razorpay Test Mode integration.

---

## Decomposed Units

### Unit 01: Core Domain Models & Config
- **Files:** `requirements.txt`, `app/config.py`, `app/models/domain.py`, `app/models/razorpay_models.py`
- **Goal:** Define immutable Pydantic schemas for `Product`, `OrderIntent`, `GuardrailResult`, `AuditRecord`, and typed Razorpay payloads.

### Unit 02: Mock Catalog & Guardrail Firewall
- **Files:** `app/services/catalog_service.py`, `app/core/guardrails.py`, `app/core/exceptions.py`
- **Goal:** Build an in-memory machine-readable product catalog and a strict middleware that validates spend limits ($\le$ ₹15,000) and discount bounds.

### Unit 03: Razorpay Payment Service
- **Files:** `app/services/payment_service.py`
- **Goal:** Integrate `razorpay` Python SDK to create sandbox orders only when receiving a `GuardrailResult(passed=True)`.

### Unit 04: Gemini Tool Calling & Agent Loop
- **Files:** `app/agents/tools.py`, `app/agents/agent.py`
- **Goal:** Implement the Buyer Agent using Gemini's native function calling to search the catalog and construct structured order intents.

### Unit 05: FastAPI Endpoints & Failure Recovery Demo
- **Files:** `app/main.py`, `app/api/routes.py`
- **Goal:** Expose `/api/v1/agentic-checkout` and build the test case demonstrating graceful failure when spending caps are breached.