# Specification: AI Model Memory & Startup Optimization (Unit 15)

## 1. Overview
The `SentenceTransformer` model (`all-MiniLM-L6-v2`) is currently instantiated inside the request lifecycle. This causes a ~150MB model to be loaded into RAM on every API call, spiking CPU and adding latency, while also triggering Hugging Face Hub token warnings. This unit fixes both by loading the model globally at server startup and suppressing the warning.

## 2. Target Files
- `app/services/semantic_catalog.py` (or the specific file where `SentenceTransformer` is imported).
- `app/main.py` (to attach the initialization to the FastAPI startup process).

## 3. Implementation Requirements

- **Suppress Warnings:** Before importing/initializing the model in your service file, set `os.environ["TOKENIZERS_PARALLELISM"] = "false"` to clean up terminal logs.
- **Global Initialization Pattern:** 
  - Remove `SentenceTransformer('all-MiniLM-L6-v2')` from the per-request search function.
  - Create a global variable `_embedding_model = None`.
  - Write a `load_embedding_model()` function that initializes the model into that global variable. 
  - Write a `get_embedding_model()` function that returns the global variable.
- **Refactor Search Logic:** Update the semantic search function to use `model = get_embedding_model()` so it utilizes the pre-loaded RAM instance.
- **FastAPI Startup Integration:** In `app/main.py`, import and call `load_embedding_model()` during the FastAPI startup phase using either `@app.on_event("startup")` or a `@asynccontextmanager` lifespan event.

## 4. Verification Steps
Before marking this task complete, you MUST:
1. Start the FastAPI server and verify the model loading logs appear *only once* during the boot process.
2. Send a POST request to `/api/v1/semantic-negotiation` and verify the model does NOT reload (no Hugging Face progress bar appears).
3. Ensure the Hugging Face `HF_TOKEN` warning is mitigated.