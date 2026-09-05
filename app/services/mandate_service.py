import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any


class MandateService:
    """Generate a tamper-evident AP2 intent mandate for verified checkout intent."""

    _secret_salt = "nexuspay-ap2-intent-mandate-v1"

    def generate_mandate(
        self,
        order_id: str,
        items: list[dict[str, Any]],
        total_amount: int,
        user_address_hash: str | None = None,
    ) -> dict[str, Any]:
        """Create a signed ACP-v1.0 mandate receipt for the order."""
        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        payload: dict[str, Any] = {
            "mandate_id": f"mandate_{uuid.uuid4()}",
            "protocol": "ACP-v1.0",
            "timestamp": timestamp,
            "order_id": order_id,
            "items": items,
            "total_amount_paise": int(total_amount) * 100,
        }
        if user_address_hash:
            payload["user_address_hash"] = user_address_hash

        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        digest = hashlib.sha256((canonical + self._secret_salt).encode("utf-8")).hexdigest()
        payload["cryptographic_signature"] = digest
        return payload
