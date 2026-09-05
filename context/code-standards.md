### 3. `context/code-standards.md`
This file tells your AI tool (Codex/Cline) exactly how to format the Python code, ensuring it writes like a senior engineer.

```markdown
# NexusPay: Code Standards & AI Rules

## 1. Python Typing & Linting
- **Strict Type Hints:** Every function signature must have explicit Python type hints for arguments and return types. 
- **Pydantic Validation:** Rely on Pydantic's `Field` constraints (e.g., `Field(ge=0, le=15000)`) to enforce business rules natively. 
- **No `Any`:** Never use `typing.Any` or generic `dict` unless absolutely necessary and documented.

## 2. Error Handling & The "Failure Demo"
- **Custom Exceptions:** Use domain-specific exceptions in `app/core/exceptions.py` (e.g., `SpendLimitExceededError`, `InvalidDiscountError`).
- **Graceful Degradation:** When an external API (like Razorpay) fails, catch the error, log it to the audit trail, and return a structured JSON error response to the frontend rather than crashing the server.

## 3. The "No Direct Payment" Rule
- The coding agent is explicitly forbidden from allowing the LLM to execute `razorpay.Order.create()`. 
- The LLM must output an intent payload, which a deterministic Python function evaluates before proceeding to the payment service.

## 4. Documentation
- Write concise Google-style docstrings for all core services and guardrails.
- Every API endpoint must have clear `summary` and `response_model` definitions for FastAPI's auto-generated Swagger UI.