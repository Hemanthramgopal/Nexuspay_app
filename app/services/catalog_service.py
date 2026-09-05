import sqlite3

from app.core.exceptions import ProductNotFoundError
from app.models.domain import Product

class CatalogService:
    """Catalog service fetching from a local SQLite database."""

    def __init__(self, db_path: str = "catalog.db") -> None:
        self.db_path = db_path

    def _get_connection(self):
        """Create a connection and return rows as dictionary-like objects."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def search_products(self, query: str) -> list[Product]:
        """Return catalog entries whose names, categories, or IDs match the query."""
        normalized = (query or "").strip().lower()
        if not normalized:
            return []

        conn = self._get_connection()
        cursor = conn.cursor()
        
        # A fast SQL LIKE search
        search_term = f"%{normalized}%"
        cursor.execute(
            """
            SELECT * FROM products 
            WHERE LOWER(name) LIKE ? 
            OR LOWER(category) LIKE ? 
            OR LOWER(id) LIKE ?
            """,
            (search_term, search_term, search_term)
        )
        rows = cursor.fetchall()
        conn.close()

        matches: list[Product] = []
        for row in rows:
            matches.append(Product(
                id=row["id"],
                name=row["name"],
                price=row["base_price"], # Map DB base_price to Pydantic price
                stock=row["stock"],
                category=row["category"]
            ))
        return matches

    def get_product(self, product_id: str) -> Product:
        """Resolve a product by exact ID from the SQLite database."""
        if not product_id or not product_id.strip():
            raise ProductNotFoundError("Product id is required.")

        clean_id = product_id.strip().lower()

        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 1. Try an exact ID match first
        cursor.execute("SELECT * FROM products WHERE LOWER(id) = ?", (clean_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return Product(
                id=row["id"],
                name=row["name"],
                price=row["base_price"],
                stock=row["stock"],
                category=row["category"]
            )
            
        # 2. Fallback to SQL search if exact ID isn't found
        matches = self.search_products(clean_id)
        if matches:
            return matches[0]

        raise ProductNotFoundError(f"Product not found: {product_id}")

    def get_product_and_min_price(self, product_id: str) -> tuple[Product, int]:
        """Return a product and its authoritative minimum price from SQLite."""
        if not product_id or not product_id.strip():
            raise ProductNotFoundError("Product id is required.")

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM products WHERE LOWER(id) = ?",
            (product_id.strip().lower(),),
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            raise ProductNotFoundError(f"Product not found: {product_id}")

        return (
            Product(
                id=row["id"],
                name=row["name"],
                price=row["base_price"],
                stock=row["stock"],
                category=row["category"],
            ),
            int(row["min_price"]),
        )
