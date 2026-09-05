"""Request and response schemas for negotiated Razorpay checkout."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.domain import AuditRecord


class CreateOrderRequest(BaseModel):
    """Client request to execute checkout for an agreed product price."""

    model_config = ConfigDict(strict=True)

    product_id: str = Field(min_length=1)
    final_price: int = Field(gt=0)
    currency: Literal["INR"] = "INR"


class IntentMandate(BaseModel):
    """AP2 permission receipt with a signed, tamper-evident mandate token."""

    model_config = ConfigDict(strict=True)

    mandate_id: str
    protocol: Literal["ACP-v1.0"] = "ACP-v1.0"
    timestamp: str
    order_id: str
    items: list[dict[str, str | int]]
    total_amount_paise: int = Field(gt=0)
    cryptographic_signature: str = Field(min_length=1)
    user_address_hash: str | None = None


class CreateOrderResponse(BaseModel):
    """Server-verified Razorpay checkout order details."""

    model_config = ConfigDict(strict=True)

    success: bool
    order_id: str
    amount: int = Field(gt=0, description="Amount in whole INR.")
    currency: Literal["INR"]
    product_name: str
    payment_url: str
    audit_record: AuditRecord
    intent_mandate: IntentMandate | None = None


class AgentProduct(BaseModel):
    """Protocol-ready product metadata for AI buyers and worker agents."""

    model_config = ConfigDict(strict=True)

    id: str
    name: str
    category: str
    description: str
    base_price: int = Field(gt=0)
    min_price: int = Field(gt=0)
    stock: int = Field(ge=0)
    compatibility_tags: list[str] = Field(min_length=1)
    recommended_addon_id: str | None = None
    specifications: dict[str, str | int | float | bool]


class AgentCatalogResponse(BaseModel):
    """Versioned catalog response for external agent protocols."""

    model_config = ConfigDict(strict=True)

    success: bool
    protocol_version: str = "ACP-v1.0"
    total_products: int = Field(ge=0)
    products: list[AgentProduct]


class NegotiationPayload(BaseModel):
    """Seller decision details returned by the negotiation workflow."""

    model_config = ConfigDict(strict=True)

    agreed: bool
    final_price: int = Field(ge=0)
    message_to_buyer: str


class ComboCheckoutRequest(BaseModel):
    """Bundle request for a negotiated primary item plus a recommended addon."""

    model_config = ConfigDict(strict=True)

    primary_product_id: str = Field(min_length=1)
    primary_agreed_price: int = Field(gt=0)
    upsell_product_id: str = Field(min_length=1)


class ComboCheckoutResponse(BaseModel):
    """Validated multi-item checkout result for the combo guardrail flow."""

    model_config = ConfigDict(strict=True)

    success: bool
    order_id: str
    total_amount: int = Field(gt=0)
    currency: Literal["INR"] = "INR"
    payment_url: str
    items: list[dict[str, str | int]]
    message: str
    intent_mandate: IntentMandate | None = None


class UpsellDetails(BaseModel):
    """Generated add-on offer and the audit event that documents it."""

    model_config = ConfigDict(strict=True)

    pitch: str = Field(min_length=1)
    item_id: str = Field(min_length=1)
    price: int = Field(gt=0)
    audit_record: AuditRecord


class ActiveOrderContext(BaseModel):
    """Minimal client-held negotiation context used for confirmation turns."""

    model_config = ConfigDict(strict=True)

    product_id: str | None = None
    order_id: str | None = None
    total_amount: int | None = Field(default=None, ge=0)


class NegotiationResponse(BaseModel):
    """Typed semantic negotiation response with optional cross-sell fields."""

    model_config = ConfigDict(strict=True)

    success: bool
    product_id: str
    offered_price: int = Field(ge=0)
    addon_accepted: bool | None = None
    chat_history: list[dict[str, str]] = Field(default_factory=list)
    traces: list[dict[str, str]] = Field(default_factory=list)
    active_order: ActiveOrderContext | None = None
    negotiation: NegotiationPayload
    audit: AuditRecord
    order: CreateOrderResponse | None = None
    upsell_pitch: str | None = None
    upsell_item_id: str | None = None
    upsell_price: int | None = Field(default=None, gt=0)
    upsell_audit: AuditRecord | None = None
    provider_used: str | None = None
    model_used: str | None = None
    latency_seconds: float | None = Field(default=None, ge=0)


