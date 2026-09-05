# Spec: Unit 04 - Gemini Tool Calling & Agent Loop

## 1. Objective
Implement the `BuyerAgent` that translates a user's natural language request into a strongly typed `OrderIntent` using the `google-genai` SDK. The agent must be able to search the catalog via a defined tool and must output its final decision strictly as an `OrderIntent` Pydantic model.

## 2. Requirements & Files
- `app/agents/tools.py`
- `app/agents/agent.py`
- Modify `app/core/exceptions.py` to add `AgentExecutionError`

## 3. Exceptions (`app/core/exceptions.py`)
Add a domain-specific exception:
- `AgentExecutionError(Exception)`: Raised when the LLM fails to generate a valid `OrderIntent` or encounters an API error.

## 4. Pure Python Tools (`app/agents/tools.py`)
Create helper functions that the agent will use to interface with the `CatalogService`.
- **Function:** `search_catalog_tool(query: str) -> str`
  - *Note:* Since standard Gemini tool definitions prefer simple types, this function should instantiate the `CatalogService`, search for the query, and return a JSON-formatted string of available products (including `id`, `name`, `price`, and `stock`).

## 5. The Buyer Agent (`app/agents/agent.py`)
Create a `BuyerAgent` class.

- **Initialization (`__init__`):**
  - Accept an optional `api_key: str | None`. If not provided, load `GEMINI_API_KEY` from `app.core.config.settings`.
  - Initialize the Gemini client: `self.client = genai.Client(api_key=api_key)`.

- **Method: `process_user_intent(user_input: str) -> OrderIntent`**
  - **System Instruction:** Define a strict system prompt instructing the model that it is the NexusPay Buyer Agent. Its job is to find the user's requested item using the `search_catalog_tool`, negotiate a discount if asked (up to 15%), and return a final order intent.
  - **Execution Loop:** 
    - Use `self.client.models.generate_content(...)` with the `gemini-2.5-flash` (or `gemini-2.0-flash`) model.
    - Pass `search_catalog_tool` in the `tools` configuration.
    - Use Gemini's **Structured Outputs** feature (`response_schema=OrderIntent`) to force the final response to exactly match the `OrderIntent` Pydantic model.
  - **Error Handling:** Wrap the call in a `try...except` block and raise `AgentExecutionError` if the model fails to return a parseable intent.
  - **Return:** Return the parsed `OrderIntent` object.

## 6. Acceptance Criteria
- `BuyerAgent` initializes correctly with the `google-genai` SDK.
- The `search_catalog_tool` returns a valid string representation of the catalog.
- The agent correctly enforces the `OrderIntent` schema output.
- A mocked test confirms that when given a mock LLM response, the agent returns a valid `OrderIntent` Pydantic model.