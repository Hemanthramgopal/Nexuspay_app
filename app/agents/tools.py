import json

from app.services.catalog_service import CatalogService


def search_catalog_tool(query: str) -> str:
    """Search the local catalog and return the product IDs that are valid in NexusPay."""
    catalog = CatalogService()
    matches = catalog.search_products(query)
    return json.dumps(
        [
            {
                "id": product.id,
                "title": product.name,
                "price": product.price,
                "stock": product.stock,
                "category": product.category,
            }
            for product in matches[:5]
        ]
    )