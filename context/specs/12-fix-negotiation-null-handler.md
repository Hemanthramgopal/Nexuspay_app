# Specification: Negotiation Null-Safety & Fallback (Unit 12)

## Overview
Harden `SellerAgent` and the negotiation route against null responses from the LLM or API timeouts, ensuring clean fallback messaging instead of raw Python exceptions.

## Core Requirements

1. **`app/agents/seller_agent.py`**:
   - Safely extract content from `response.choices[0].message.content`.
   - Wrap `json.loads(content)` in a try/except block.
   - If `content` is `None`, parsing fails, or the API call raises an error, do NOT crash. Fall back gracefully to:
     ```python
     NegotiationResult(
         agreed=False,
         final_price=min_price,
         message_to_buyer=f"I cannot accept ₹{offered_price}. The minimum acceptable price is ₹{min_price}."
     )
     ```
   - Ensure environment variables for `OPENROUTER_API_KEY` (or `OPENAI_API_KEY`) are read correctly from `Settings`.

2. **`app/api/routes.py`**:
   - Ensure any exception in the agent negotiation returns a structured JSON payload with `success=False` and a human-readable rejection message, rather than a raw 500/unhandled exception string.