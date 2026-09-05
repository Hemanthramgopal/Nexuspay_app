# Specification: Seller Agent Negotiation (Unit 09)

## Overview
Implement a `SellerAgent` class that evaluates a buyer's proposed price against strict SQLite database constraints, utilizing an LLM to haggle without ever breaching the established price floor.

## Core Requirements

1. **Database Integration**: 
   - Connect to the local `catalog.db` SQLite database using `sqlite3`.
   - Create a method to extract `base_price`, `min_price`, and `stock` for a given `product_id`.

2. **Model Configuration**: 
   - Utilize the `nvidia/nemotron-3-ultra-550b-a55b:free` model via the OpenAI SDK targeting the OpenRouter base URL.
   - Credentials must be pulled from `Settings` in `app/core/config.py`.

3. **Negotiation Logic**:
   - **Auto-Accept**: If `offered_price` >= `base_price`, bypass the LLM entirely and return an immediate acceptance.
   - **AI Negotiation**: Instruct the LLM via system prompt to haggle if the offer is below the base price. It must counter-offer if the price is below the `min_price` floor.

4. **Hard Guardrails (Crucial for Razorpay Evaluation)**: 
   - Implement a deterministic Python check *after* the LLM response is parsed. 
   - If the LLM hallucinates and sets `agreed=True` with a `final_price` < `min_price`, programmatically override it to `agreed=False`, set the price to `min_price`, and inject a system fallback message.

5. **Output Schema**: 
   - Create and use a Pydantic model `NegotiationResult` containing: `agreed` (bool), `final_price` (int), and `message_to_buyer` (str).