from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Product(BaseModel):
    """A catalog product available for purchase."""

    model_config = ConfigDict(strict=True)

    id: str
    name: str
    price: int = Field(gt=0)
    stock: int = Field(ge=0)
    category: str


class CartItem(BaseModel):
    """A product and quantity included in a checkout cart."""

    model_config = ConfigDict(strict=True)

    product_id: str
    quantity: int = Field(gt=0)


class OrderIntent(BaseModel):
    """A structured purchase request produced by the buyer agent."""

    model_config = ConfigDict(strict=True)

    items: list[CartItem] = Field(min_length=1)
    requested_discount_percent: int = Field(default=0, ge=0, le=100)


class GuardrailResult(BaseModel):
    """The deterministic result of validating an order intent."""

    model_config = ConfigDict(strict=True)

    passed: bool
    reason: str | None = None
    final_price: int | None = None


class AuditRecord(BaseModel):
    """A typed record of an agentic checkout step."""

    model_config = ConfigDict(strict=True)

    step: str
    action: str
    status: Literal["SUCCESS", "FAILED", "BLOCKED"]
    details: str
    timestamp: datetime