import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_TOKEN"] = "local-dev-token"  # Changed from setdefault to direct assignment
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

import json
import sqlite3

import numpy as np
from sentence_transformers import SentenceTransformer

from app.models.schemas import AgentProduct

_embedding_model = None


def get_agent_products(db_path: str = "catalog.db") -> list[AgentProduct]:
    """Return catalog products with JSON metadata decoded for agent consumers."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT id, name, category, description, base_price, min_price, stock,
               compatibility_tags, recommended_addon_id, specifications
        FROM products
        ORDER BY id
        """
    ).fetchall()
    conn.close()

    return [
        AgentProduct(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            description=row["description"],
            base_price=row["base_price"],
            min_price=row["min_price"],
            stock=row["stock"],
            compatibility_tags=json.loads(row["compatibility_tags"]),
            recommended_addon_id=row["recommended_addon_id"],
            specifications=json.loads(row["specifications"]),
        )
        for row in rows
    ]


def load_embedding_model() -> SentenceTransformer:
    """Load the lightweight embedding model once into process memory."""
    global _embedding_model
    if _embedding_model is None:
        print("Loading semantic embedding model into memory...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def get_embedding_model() -> SentenceTransformer:
    """Return the global embedding model instance, lazily creating it if needed."""
    return _embedding_model if _embedding_model is not None else load_embedding_model()


class SemanticCatalog:
    """Vector search engine for the product catalog."""

    def __init__(self, db_path: str = "catalog.db") -> None:
        self.db_path = db_path
        self.model = get_embedding_model()
        self._build_index()

    def _build_index(self) -> None:
        """Load products from SQLite and pre-compute their vector embeddings."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, name, category, description, compatibility_tags, specifications
            FROM products
            """
        ).fetchall()
        conn.close()

        self.ids = []
        texts = []
        for row in rows:
            self.ids.append(row["id"])
            texts.append(
                f"{row['name']} - Category: {row['category']} - Description: {row['description']} "
                f"- Compatibility: {', '.join(json.loads(row['compatibility_tags']))} "
                f"- Specifications: {json.dumps(json.loads(row['specifications']))}"
            )

        self.product_vectors = self.model.encode(texts)

    def search(self, query: str) -> str:
        """Embed the query and return the closest product ID using cosine similarity."""
        query_vector = self.model.encode(query)

        norms = np.linalg.norm(self.product_vectors, axis=1) * np.linalg.norm(query_vector)
        similarities = np.dot(self.product_vectors, query_vector) / norms

        best_idx = np.argmax(similarities)
        return self.ids[best_idx]
