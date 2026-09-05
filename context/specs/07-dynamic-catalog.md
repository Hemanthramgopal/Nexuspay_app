# Spec: Unit 07 - Dynamic External Merchant Catalog

## 1. Objective
Replace the static, hardcoded product dictionary with a live HTTP client that fetches real product data from the DummyJSON public API. This aligns the architecture with UAP/AP2 external merchant data feeds.

## 2. Requirements & Files
- Update `requirements.txt` to include `httpx`.
- Modify `app/agents/tools.py`.

## 3. Implementation Details
- **HTTP Client:** Import `httpx`.
- **Update `search_catalog_tool`:**
  - The tool should take a `query` string.
  - Make a `GET` request to `https://dummyjson.com/products/search?q={query}`.
  - Extract the `products` array from the JSON response.
  - Map the DummyJSON fields to our internal format. 
    - Since DummyJSON prices are low (e.g., $19.99), multiply the price by 80 to simulate a realistic INR (₹) base price for the Razorpay gateway.
  - Return a formatted string or lightweight dictionary of the top 3-5 matching products (ID, Title, Price in INR, Stock) so the Gemini agent can easily read it and construct the `OrderIntent`.

## 4. Acceptance Criteria
- Running `pip install -r requirements.txt` successfully installs `httpx`.
- When a user asks for a "laptop" or "smartphone" in the UI, the backend successfully fetches real DummyJSON products, applies the guardrails, and creates a Razorpay order.