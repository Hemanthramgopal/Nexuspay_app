# NexusPay: Project Overview

## 1. Product Objective
NexusPay is a deterministic, AI-driven Agentic Commerce gateway designed for the Razorpay AI Buildathon 2026. It allows an AI Buyer Agent to interpret a user's natural language intent, query a machine-readable merchant catalog, negotiate bundles, and securely execute a transaction using Razorpay Test APIs. 

## 2. Business Context & Alignment
The project aligns with NPCI's Unified Agent Protocol (UAP) and Razorpay's 2026 Agentic Payments pilots. It solves the critical "Human-in-the-Loop" bottleneck in AI commerce by replacing manual PINs/OTPs with a pre-authorized, bounded spend limit (inspired by UPI Reserve Pay).

## 3. The Razorpay Evaluation Bar (Strict Guardrails)
- **Bounded Money Actions:** The AI must NEVER call payment APIs directly. It must construct an `OrderIntent`, which is verified by a deterministic Python Guardrail Interceptor.
- **Explainability:** Every AI decision and tool call must emit a typed `AuditLog` event.
- **Graceful Failure:** The system must intentionally demonstrate a failure state (e.g., the AI hallucinating a discount larger than the allowed margin) and show the Guardrail Interceptor catching it, aborting the payment, and alerting the user.

## 4. User Flow (The Steel Thread)
1. **User Prompt:** "Find me a mechanical keyboard under ₹4,000 and order it."
2. **Agent Reasoning:** Buyer Agent extracts intent, price bounds, and item category.
3. **Tool Call:** Agent calls `query_agentic_catalog`.
4. **Draft Order:** Agent calls `draft_order` with the selected Product ID.
5. **Guardrail Intercept:** A deterministic middleware checks if the cart total exceeds ₹4,000. 
6. **Payment Execution:** If passed, the Payment Service calls `razorpay.Order.create()` (Test Mode).
7. **Audit Emitted:** The frontend visualizes the step-by-step trace and payment link.

## 5. Out of Scope for v1
- Real money transactions (Sandbox ONLY).
- Multi-merchant marketplace logic.
- Voice/Hinglish inputs.