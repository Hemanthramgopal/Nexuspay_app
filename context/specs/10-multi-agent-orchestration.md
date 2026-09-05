# Specification: Multi-Agent Orchestration (Unit 10)

## Overview
Wire the newly created `SellerAgent` and the `SemanticCatalog` into the main FastAPI endpoint. The system must orchestrate a handoff between the semantic search, the buyer's requested price, and the seller's negotiation logic.

## Core Requirements

1. **Service Initialization**: 
   - Instantiate `SemanticCatalog` and `SellerAgent` in the API router/controller where checkout requests are handled.

2. **The Multi-Agent Loop**:
   - **Step 1 (Intent & Search)**: Extract the requested product and desired price from the user's prompt. Pass the product description to `SemanticCatalog.search()` to get the deterministic `product_id`.
   - **Step 2 (Handoff)**: Pass the resolved `product_id` and the user's requested price to `SellerAgent.negotiate()`.
   
3. **API Response**:
   - The endpoint must return a structured JSON response containing the `NegotiationResult` (agreed status, final price, and the seller's message to the buyer).
   - Ensure the transaction trace (Audit Log) captures both the semantic match and the negotiation outcome.

4. **Error Handling**:
   - If the `SellerAgent` raises an `AgentExecutionError` or rejects the price (`agreed=False`), the API must catch this and return a 400 Bad Request with the seller's strict rejection message, preventing any payment gateway execution.