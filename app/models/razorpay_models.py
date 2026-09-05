from pydantic import BaseModel, ConfigDict, Field


class RazorpayOrderRequest(BaseModel):
    """Typed request payload for creating a Razorpay order."""

    model_config = ConfigDict(strict=True)

    amount: int = Field(gt=0)
    currency: str = "INR"
    notes: dict[str, str]


class RazorpayOrderResponse(BaseModel):
    """Typed response payload returned by Razorpay order creation."""

    model_config = ConfigDict(strict=True)

    id: str
    entity: str
    amount: int = Field(gt=0)
    status: str
