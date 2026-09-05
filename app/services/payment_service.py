from datetime import datetime, timezone

import razorpay

from app.core.config import Settings
from app.core.exceptions import PaymentServiceError
from app.models.domain import AuditRecord, GuardrailResult, OrderIntent, Product
from app.models.razorpay_models import RazorpayOrderRequest, RazorpayOrderResponse
from app.services.catalog_service import CatalogService


settings = Settings()
MOCK_PAYMENT_URL = "https://rzp.io/i/mock_or_test_link"


class PaymentService:
    """Create Razorpay sandbox orders after guardrail approval."""

    def __init__(
        self,
        key_id: str | None = None,
        key_secret: str | None = None,
    ) -> None:
        resolved_key_id = key_id or settings.RAZORPAY_KEY_ID
        resolved_key_secret = key_secret or settings.RAZORPAY_KEY_SECRET
        try:
            self.client = razorpay.Client(auth=(resolved_key_id, resolved_key_secret))
        except Exception as error:
            raise PaymentServiceError(
                f"Razorpay client initialization failed: {str(error)}"
            ) from error

    def create_payment_order(
        self,
        intent: OrderIntent,
        products: list[Product],
        guardrail_result: GuardrailResult,
    ) -> tuple[RazorpayOrderResponse, AuditRecord]:
        """Create an order only when deterministic guardrails approve it."""
        if not guardrail_result.passed or guardrail_result.final_price is None:
            raise PaymentServiceError(
                "Cannot initiate payment on unverified or failed order intent."
            )

        amount_in_paise = guardrail_result.final_price * 100
        request = RazorpayOrderRequest(
            amount=amount_in_paise,
            currency="INR",
            notes={
                "product_ids": ",".join(product.id for product in products),
                "quantities": ",".join(
                    str(item.quantity) for item in intent.items
                ),
                "discount": str(intent.requested_discount_percent),
            },
        )

        try:
            response_data = self.client.order.create(data=request.model_dump())
            response = RazorpayOrderResponse.model_validate(response_data)
        except Exception as error:
            raise PaymentServiceError(
                f"Razorpay order creation failed: {str(error)}"
            ) from error

        audit_record = AuditRecord(
            step="PAYMENT_GATEWAY",
            action="CREATE_ORDER",
            status="SUCCESS",
            details=(
                f"Created Razorpay order {response.id} for amount "
                f"₹{guardrail_result.final_price}"
            ),
            timestamp=datetime.now(timezone.utc),
        )
        return response, audit_record

    def create_negotiated_order(
        self,
        product_id: str,
        final_price: int,
        currency: str = "INR",
    ) -> tuple[RazorpayOrderResponse, Product, AuditRecord]:
        """Create an order after independently re-verifying the database price floor."""
        if currency != "INR":
            raise PaymentServiceError("Only INR Razorpay orders are supported.")

        product, min_price = CatalogService().get_product_and_min_price(product_id)
        if final_price < min_price:
            raise PaymentServiceError(
                "Negotiated price is below the server-verified minimum price."
            )

        amount_in_paise = final_price * 100
        request = RazorpayOrderRequest(
            amount=amount_in_paise,
            currency=currency,
            notes={
                "product_id": product.id,
                "final_price_inr": str(final_price),
                "min_price_verified": "true",
            },
        )

        try:
            response_data = self.client.order.create(data=request.model_dump())
            response = RazorpayOrderResponse.model_validate(response_data)
        except Exception as error:
            raise PaymentServiceError(
                f"Razorpay order creation failed: {str(error)}"
            ) from error

        audit_record = AuditRecord(
            step="ORDER_CREATED",
            action="CREATE_RAZORPAY_ORDER",
            status="SUCCESS",
            details=(
                f"Razorpay order created for ₹{final_price:,} "
                f"(Order ID: {response.id})"
            ),
            timestamp=datetime.now(timezone.utc),
        )
        return response, product, audit_record

    def create_payment_link(
        self,
        amount: int,
        description: str,
        reference_id: str,
        currency: str = "INR",
    ) -> str:
        """Create a hosted Razorpay payment link, with a demo fallback when unavailable."""
        key_id = getattr(settings, "RAZORPAY_KEY_ID", "")
        key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "")
        if not key_id or not key_secret:
            return MOCK_PAYMENT_URL

        try:
            response_data = self.client.payment_link.create(
                data={
                    "amount": amount * 100,
                    "currency": currency,
                    "accept_partial": False,
                    "description": description,
                    "reference_id": reference_id,
                    "callback_url": "http://localhost:5173/success",
                    "callback_method": "get",
                }
            )
            if not isinstance(response_data, dict):
                raise PaymentServiceError("Razorpay returned an invalid payment link response.")
            payment_url = response_data.get("short_url")
            if not isinstance(payment_url, str) or not payment_url:
                raise PaymentServiceError("Razorpay did not return a payment link URL.")
            return payment_url
        except Exception:
            return MOCK_PAYMENT_URL
