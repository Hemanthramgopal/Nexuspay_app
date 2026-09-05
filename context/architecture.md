# NexusPay: System Architecture

## 1. Tech Stack
- **API Framework:** FastAPI (Python 3.11+)
- **Data Validation:** Pydantic v2 (Strict typing is mandatory)
- **AI Orchestration:** Google GenAI SDK (Gemini 1.5/2.0 Flash) with native Tool Calling
- **Payment Layer:** Razorpay Python SDK
- **Logging:** Standard Python logging + JSON Audit trail

## 2. Domain-Driven Directory Structure
The codebase must adhere to this structure. Do not put all logic in `main.py`.
```text
nexuspay/
├── app/
│   ├── api/          # FastAPI routes
│   ├── agents/       # LLM prompts, state loops, and Tool definitions
│   ├── core/         # Guardrails, Exceptions, Config (env vars)
│   ├── models/       # Pydantic domain schemas (Single source of truth)
│   ├── services/     # Pure Python logic (Catalog mock DB, Razorpay SDK calls)
│   └── main.py       # App initialization