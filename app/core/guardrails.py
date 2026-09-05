from app.core.config import Settings
from app.models.domain import GuardrailResult, OrderIntent, Product

settings = Settings()

def verify_order_intent(
    intent: OrderIntent,
    products: list[Product],
) -> GuardrailResult:
    """Validate stock, discount, and total spend for an order intent."""
    if intent.requested_discount_percent > settings.MAX_DISCOUNT_PERCENT:
        return GuardrailResult(
            passed=False,
            reason=(
                "Discount exceeds maximum allowed percentage: "
                f"{settings.MAX_DISCOUNT_PERCENT}%"
            ),
        )

    if len(products) != len(intent.items):
        return GuardrailResult(
            passed=False,
            reason="Cart products do not match the requested cart items.",
        )

    gross_price = 0
    for item, product in zip(intent.items, products):
        if item.quantity > product.stock:
            return GuardrailResult(
                passed=False,
                reason=(
                    f"Insufficient stock for {product.name}: requested "
                    f"{item.quantity}, available {product.stock}"
                ),
            )
        gross_price += product.price * item.quantity

    final_price = (
        gross_price * (100 - intent.requested_discount_percent)
    ) // 100
    if final_price > settings.MAX_SPEND_LIMIT:
        return GuardrailResult(
            passed=False,
            reason=(
                f"Spend limit exceeded: final price ₹{final_price} exceeds "
                f"₹{settings.MAX_SPEND_LIMIT}"
            ),
        )

    return GuardrailResult(passed=True, final_price=final_price)