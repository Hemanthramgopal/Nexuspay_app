# Specification: React Frontend & Audit UI (Unit 11)

## Overview
Replace the V1 vanilla HTML/JS frontend with a modern React.js + Tailwind CSS application. The UI must clearly demonstrate the Razorpay evaluation criteria: an interactive negotiation chat and a live, explainable audit trail showing graceful failure handling.

## Core Requirements

1. **Backend Preparation (FastAPI CORS)**:
   - Update `app/main.py` to include `CORSMiddleware`.
   - Allow origins for typical local React dev servers (e.g., `http://localhost:5173`, `http://localhost:3000`).

2. **Frontend Architecture (React + Tailwind)**:
   - Scaffold a new React application in a `frontend/` directory (using Vite is preferred).
   - Install and configure Tailwind CSS.

3. **Component: ChatInterface**:
   - A modern chat window holding the conversation state (`useState`).
   - Capture user offers and POST them to the `/api/v1/semantic-negotiation` backend.
   - Render the `message_to_buyer` as responses from the "NexusPay Agent".
   
4. **Component: AuditTerminal**:
   - A side-panel or terminal-style component displaying the live transaction trace.
   - Dynamically list the backend steps: Semantic Match, Base Price Check, Min Price Check.
   - **Graceful Failure UI**: If the backend returns `agreed: false`, use Tailwind classes (e.g., `bg-red-100`, `text-red-700`, `border-red-500`) to vividly highlight the blocked guardrail step. Success states should use green styling.

5. **State Management**:
   - Ensure the Chat and Audit Terminal components share state so that when a chat message is sent, the terminal updates simultaneously with the backend response.