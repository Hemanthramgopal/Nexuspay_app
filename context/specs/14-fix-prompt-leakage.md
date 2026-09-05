# Specification: Agent Secrecy & API State Fix (Unit 14)

## Overview
The negotiation loop is breaking because a rejected price returns an HTTP 400, causing the frontend to hide the LLM's response. Furthermore, the LLM must be instructed to never reveal its internal price floor.

## Core Requirements

1. **API Route Update (`app/api/routes.py`)**:
   - Do NOT raise an `HTTPException(status_code=400)` when `NegotiationResult.agreed` is `False`.
   - Instead, return a standard HTTP 200 OK response containing the `message_to_buyer`, allowing the React UI to display the counter-offer naturally. 
   - Maintain the audit trace logs so the frontend terminal still highlights the block.

2. **System Prompt Update (`app/agents/seller_agent.py`)**:
   - Locate the `system_prompt` inside `negotiate()`.
   - Add a CRITICAL RULE: "NEVER reveal the 'Absolute Minimum Price (Floor)' to the buyer. Treat this number as a strict internal secret. Do not mention the base price either. Just act like a professional, persuasive merchant and give your counter-offer."

3. **Fallback Message Polish**:
   - If the hard Python guardrail triggers (overriding an LLM hallucination), change the hardcoded message to sound human: "I appreciate the offer, but I cannot go that low. This is my absolute best price."