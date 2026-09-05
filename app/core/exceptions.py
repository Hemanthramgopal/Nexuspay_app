class CatalogError(Exception):
    """Base exception for catalog domain errors."""


class ProductNotFoundError(CatalogError):
    """Raised when a requested product is not in the catalog."""


class GuardrailViolationError(Exception):
    """Raised for guardrail domain errors outside result-based validation."""


class PaymentServiceError(Exception):
    """Raised when Razorpay order creation cannot be completed."""


class AgentExecutionError(Exception):
    """Raised when the buyer agent cannot produce a valid order intent."""
