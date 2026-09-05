# Spec: Unit 06 - Frontend Dashboard

## 1. Objective
Build a split-screen frontend interface to visualize the NexusPay v1 backend. It must serve as a static HTML file via FastAPI, demonstrating the consumer chat on one side and the real-time JSON audit trace on the other.

## 2. Requirements & Files
- `app/static/index.html`
- `app/static/style.css`
- `app/static/app.js`
- Modify `app/main.py` to serve static files.

## 3. UI Design (Tailwind CSS)
- **Layout:** A two-column CSS grid.
- **Left Column (Chat/Input):** 
  - A text input field and a "Send" button.
  - A message area showing user queries and agent responses.
  - If a Razorpay payment link is generated, display it as a clickable button.
- **Right Column (Audit Terminal):**
  - A dark-themed, monospace container.
  - Displays the raw `CheckoutResponse` JSON returned by the API.
  - Must clearly highlight `GuardrailResult` status (e.g., green for passed, red for blocked).

## 4. API Integration (`app/static/app.js`)
- Write an async function that sends a `POST` request to `/api/v1/agentic-checkout`.
- Handle the loading state (disable the button while waiting for the Gemini/Razorpay response).
- Parse the response: update the Left Column with the human-readable outcome and dump the raw JSON into the Right Column.

## 5. FastAPI Integration (`app/main.py`)
- Mount a `StaticFiles` directory to serve the frontend at the root `/`.

## 6. Acceptance Criteria
- Loading `http://localhost:8000/` in a browser displays the UI.
- Submitting an order > ₹15,000 updates the terminal with the `BLOCKED` audit log without crashing the UI.