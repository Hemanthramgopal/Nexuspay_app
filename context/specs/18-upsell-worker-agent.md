# Specification: Upsell Worker Agent (Unit 18)

## 1. Overview
To satisfy the "grow merchant revenue" requirement of the Razorpay track, we are implementing a multi-agent workflow. When the Master Seller Agent successfully negotiates a price for a primary item, it hands off to an Upsell Worker Agent. The Worker Agent uses the `recommended_addon_id` from the newly enriched catalog to generate a persuasive, AI-driven cross-sell pitch appended directly to the checkout payload.

## 2. Target Files
- `app/agents/upsell_agent.py` (New file for the Worker Agent)
- `app/api/routes.py` (Update the negotiation success path)
- `app/models/schemas.py` (Update the negotiation response schema)
- `frontend/src/components/ChatInterface.jsx` (Render the upsell pitch in the UI)
- `frontend/src/components/AuditTerminal.jsx` (Log the upsell attempt)

## 3. Implementation Requirements

### 3.1. The Upsell Worker Agent (`upsell_agent.py`)
- Create a new class `UpsellAgent`.
- Implement a method `generate_pitch(primary_item_name: str, addon_item_name: str, addon_price: int) -> str`.
- Use the LLM to generate a single, highly persuasive, 1-2 sentence cross-sell pitch. 
- *System Prompt Rule:* "You are an expert e-commerce cross-sell agent. The buyer just agreed to buy [primary_item]. Pitch them the [addon_item] for [addon_price]. Keep it to exactly one short sentence. Do not mention discounts unless explicitly told."

### 3.2. Response Schema Update (`schemas.py`)
Update the success payload (e.g., `NegotiationResponse`) to include optional upsell fields:
```python
class NegotiationResponse(BaseModel):
    # ... existing fields ...
    upsell_pitch: Optional[str] = None
    upsell_item_id: Optional[str] = None
    upsell_price: Optional[int] = None

3.3. API Route Update (routes.py)
In the semantic-negotiation route, when agreed == True:

Fetch the primary product's recommended_addon_id from catalog.db.

If an add-on exists, query catalog.db for the add-on's name and base_price.

Call the UpsellAgent.generate_pitch() method.

Attach the generated pitch, ID, and price to the final JSON response alongside the Razorpay order_id.

Add an audit log step: UPSELL_PITCH_GENERATED.

3.4. React UI Update (ChatInterface.jsx & AuditTerminal.jsx)
ChatInterface: If the response contains an upsell_pitch, render it inside the checkout card, just above the Razorpay button. Add a secondary "Add to Order (₹X)" button next to the standard checkout button. (Note: For this unit, the "Add to Order" button can just console.log or show a "Coming Soon" toast—we will wire the combo transaction in Unit 19).

AuditTerminal: Render a yellow/amber audit block for UPSELL_PITCH_GENERATED to visually prove the worker agent was triggered.

4. Verification Steps
Before marking this task complete, you MUST:

Submit an offer of ₹4,000 for a "gaming keyboard" to trigger a successful negotiation.

Verify the backend response includes the Razorpay order_id AND the upsell_pitch for the "ergonomic_mouse" (or the respective add-on).

Verify the React UI displays the AI-generated pitch and the secondary "Add to Order" button inside the checkout card.

Verify the Audit Terminal logs the yellow UPSELL_PITCH_GENERATED event.