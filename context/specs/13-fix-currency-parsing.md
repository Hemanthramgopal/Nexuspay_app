# Specification: Currency Parsing Fix (Unit 13)

## Overview
The intent extraction logic is failing to parse numbers with commas (e.g., "3,200" is being parsed as "200"). Sanitize the user prompt before extracting the offered price.

## Core Requirements

1. **Locate Price Extraction**:
   - Find where the user's prompt is parsed for the `offered_price` (likely in `app/api/routes.py` or `app/agents/buyer_agent.py`).

2. **Sanitize Input**:
   - Before running regex or passing it to the LLM to extract the price, strip commas from the input string if they are surrounded by digits. 
   - Example in Python: `sanitized_prompt = prompt.replace(',', '')` or using a better regex like `re.search(r'\d+(?:,\d+)*', prompt)`.

3. **Validation**:
   - The parser must correctly identify `3200` from the string `"₹3,200"` or `"3,200"`.