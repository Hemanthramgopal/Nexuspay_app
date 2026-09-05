# Specification: Agent-Readable Catalog & Schema Enrichment (Unit 17)

## 1. Overview
To enable downstream AI agents (such as the upcoming Upsell Worker Agent) and external AI buyers to understand product compatibility, relationships, and protocol-standardized metadata, the SQLite database catalog must be upgraded. This unit adds machine-readable compatibility tags, recommended add-on IDs, and structured JSON-LD specifications to `catalog.db`, alongside an endpoint that serves this structured catalog.

## 2. Target Files
- `setup_catalog.py` (or whatever script initializes/migrates `catalog.db`)
- `app/services/semantic_catalog.py` (update model retrieval and SQL query mapping)
- `app/models/schemas.py` (add agent-readable product and catalog schemas)
- `app/api/routes.py` (expose a dedicated `GET /api/v1/agent-catalog` endpoint)

## 3. Implementation Requirements

### 3.1. Database Schema Migration
Update the `products` table in `catalog.db` to include structured metadata fields:

```sql
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    base_price INTEGER NOT NULL,
    min_price INTEGER NOT NULL,
    stock INTEGER NOT NULL,
    compatibility_tags TEXT NOT NULL, -- JSON array string, e.g. '["usb-c", "mechanical", "ergonomic"]'
    recommended_addon_id TEXT,        -- Foreign ID of best cross-sell pairing, e.g. 'ergonomic_mouse'
    specifications TEXT               -- JSON object string with machine-readable hardware specs
);

3.2. Enriched Seed Data
Update the database seed dataset to link products with clear upsell pairings and compatibility tags:

smartphone:

compatibility_tags: ["usb-c", "fast-charging", "mobile"]

recommended_addon_id: "usb_c_charger"

specifications: {"os": "Android", "display": "6.7 inch OLED", "charging_wattage": 65}

laptop:

compatibility_tags: ["usb-c", "thunderbolt", "workstation"]

recommended_addon_id: "premium_monitor"

specifications: {"ram": "32GB", "processor": "M3-tier", "storage": "1TB SSD"}

mechanical_keyboard_87keys:

compatibility_tags: ["mechanical", "usb-c", "gaming", "desk-setup"]

recommended_addon_id: "ergonomic_mouse"

specifications: {"switches": "Tactile Blue", "layout": "Tenkeyless 87-key", "rgb": true}

premium_monitor:

compatibility_tags: ["4k", "hdmi", "displayport", "usb-c"]

recommended_addon_id: "mechanical_keyboard_87keys"

specifications: {"resolution": "3840x2160", "refresh_rate": "144Hz", "panel": "IPS"}

(Ensure all other catalog items have non-null default tags and realistic specifications).

3.3. Pydantic Schemas (app/models/schemas.py)
Add typed models for the agent-readable catalog representation:

Python
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class AgentProduct(BaseModel):
    id: str
    name: str
    category: str
    description: str
    base_price: int
    min_price: int
    stock: int
    compatibility_tags: List[str]
    recommended_addon_id: Optional[str] = None
    specifications: Dict[str, Any]

class AgentCatalogResponse(BaseModel):
    success: bool
    protocol_version: str = "ACP-v1.0"
    total_products: int
    products: List[AgentProduct]
3.4. Expose Agent-Readable Endpoint (app/api/routes.py)
Implement GET /api/v1/agent-catalog.

Query catalog.db, parse JSON fields (compatibility_tags and specifications), and return a typed AgentCatalogResponse.

Ensure existing /api/v1/semantic-negotiation and /api/v1/create-order continue to work without breaking.

4. Verification Steps
Before marking this task complete, you MUST:

Re-run database setup to verify catalog.db updates cleanly without SQL syntax errors.

Send a GET request to http://127.0.0.1:8011/api/v1/agent-catalog and verify:

Status code is 200 OK.

protocol_version is "ACP-v1.0".

Each product includes parsed lists for compatibility_tags and a valid recommended_addon_id.

Verify that the previous negotiation flow (POST /api/v1/semantic-negotiation) still functions seamlessly.