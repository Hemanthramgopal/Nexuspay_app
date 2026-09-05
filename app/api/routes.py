import re
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.agents.agent import BuyerAgent
from app.agents.seller_agent import NegotiationResult, SellerAgent
from app.agents.upsell_agent import UpsellAgent
from app.core.exceptions import AgentExecutionError, CatalogError, PaymentServiceError
from app.models.domain import AuditRecord, GuardrailResult, OrderIntent
from app.models.razorpay_models import RazorpayOrderRequest, RazorpayOrderResponse
from app.models.schemas import (
    AgentCatalogResponse,
    ActiveOrderContext,
    ComboCheckoutRequest,
    ComboCheckoutResponse,
    CreateOrderRequest,
    CreateOrderResponse,
    NegotiationResponse,
    UpsellDetails,
)
from app.services.catalog_service import CatalogService
from app.core.guardrails import verify_order_intent
from app.services.mandate_service import MandateService
from app.services.payment_service import PaymentService
from app.services.semantic_search import SemanticCatalog, get_agent_products


class CheckoutRequest(BaseModel):
    """Request containing the user's natural-language checkout prompt."""

    prompt: str


class CheckoutResponse(BaseModel):
    """Typed result of the agentic checkout pipeline."""

    success: bool
    intent: OrderIntent | None = None
    guardrail_result: GuardrailResult | None = None
    payment_order: RazorpayOrderResponse | None = None
    audit: AuditRecord
    provider_used: str | None = None
    model_used: str | None = None
    latency_seconds: float | None = None


class NegotiationRequest(BaseModel):
    """Request payload for semantic product matching and seller negotiation."""

    prompt: str
    chat_history: list[dict[str, str]] = Field(default_factory=list)
    active_order: ActiveOrderContext | None = None


OUT_OF_DOMAIN_RESPONSE = (
    "I specialize in NexusPay product negotiations and checkout. I cannot assist with anything beyond that. "
    "Let's get back to the catalog—what are you looking to purchase today?"
)
INCOMPLETE_PRODUCT_RESPONSE = (
    "Hi! I can help you find and negotiate a NexusPay product. "
    "What would you like to purchase today?"
)


def _is_out_of_domain(prompt: str) -> bool:
    """Reject non-commerce requests and prompt-injection attempts before catalog search."""
    normalized = prompt.lower()
    injection_terms = (
        "ignore all previous instructions",
        "ignore previous instructions",
        "previous instructions",
        "write a script",
        "system prompt",
        "bypass",
        "jailbreak",
        "developer message",
        "api key",
        "api keys",
        "access key",
        "secret key",
        "secret",
        "password",
        "reveal",
        "token",
        "leak",
    )
    if any(term in normalized for term in injection_terms):
        return True

    non_commerce_terms = (
        "write code", "python code", "javascript", "recipe", "cook", "essay", "poem",
        "story", "translate", "summarize", "debug", "program", "homework",
    )
    commerce_terms = ("buy", "purchase", "order", "need", "looking for", "want", "price", "₹", "rs")
    return any(term in normalized for term in non_commerce_terms) and not any(
        term in normalized for term in commerce_terms
    )


def _is_incomplete_product_request(prompt: str) -> bool:
    """Prevent greetings and standalone acknowledgements from matching a product by proximity."""
    normalized = re.sub(r"[^a-z\s]", "", prompt.lower()).strip()
    return normalized in {
        "hi", "hello", "hey", "hii", "sup", "howdy", "whats up", "what is up",
        "good morning", "good afternoon", "good evening",
    }


def _addon_was_declined(prompt: str) -> bool:
    """Detect explicit buyer rejection of an accessory or upsell."""
    normalized = prompt.lower()
    rejection_terms = ("don't want", "do not want", "no headphones", "skip the", "without the", "don't add")
    addon_terms = ("headphone", "mouse", "charger", "accessory", "addon", "add-on")
    return any(term in normalized for term in rejection_terms) and any(
        term in normalized for term in addon_terms
    )


def _is_confirmation(prompt: str) -> bool:
    """Identify short buyer confirmations that should reuse the active product."""
    normalized = re.sub(r"[^a-z0-9\s]", "", prompt.lower()).strip()
    return bool(
        re.fullmatch(
            r"(?:yes(?:\s+lets proceed)?|ok(?:ay)?|sure|proceed|lets proceed|go ahead|accept)(?:\s+with(?:\s+the)?\s+\d[\d,]*)?(?:\s+then)?",
            normalized,
        )
    )


def _is_price_offer(prompt: str) -> bool:
    """Identify a buyer message containing a numeric offer for the active negotiation."""
    return bool(re.search(r"\d[\d,]*", prompt))

router = APIRouter()


@router.get(
    "/api/v1/agent-catalog",
    response_model=AgentCatalogResponse,
    summary="Return the agent-readable, protocol-ready product catalog",
)
def get_agent_catalog() -> AgentCatalogResponse:
    """Serve catalog metadata for AI buyers and downstream worker agents."""
    products = get_agent_products()
    return AgentCatalogResponse(
        success=True,
        total_products=len(products),
        products=products,
    )


def _create_negotiated_order_response(
    product_id: str,
    final_price: int,
    currency: str = "INR",
) -> CreateOrderResponse:
    """Build a checkout response after the payment service verifies the price floor."""
    payment_order, product, audit_record = PaymentService().create_negotiated_order(
        product_id=product_id,
        final_price=final_price,
        currency=currency,
    )
    mandate = MandateService().generate_mandate(
        order_id=payment_order.id,
        items=[{"product_id": product.id, "quantity": 1}],
        total_amount=final_price,
    )
    payment_url = PaymentService().create_payment_link(
        amount=final_price,
        description=f"NexusPay checkout for {product.name}",
        reference_id=payment_order.id,
        currency=currency,
    )
    return CreateOrderResponse(
        success=True,
        order_id=payment_order.id,
        amount=final_price,
        currency=currency,
        product_name=product.name,
        payment_url=payment_url,
        audit_record=audit_record,
        intent_mandate=mandate,
    )


def _create_upsell_details(product_id: str) -> UpsellDetails | None:
    """Generate an add-on pitch from the database relationship for an agreed product."""
    products = {product.id: product for product in get_agent_products()}
    primary_product = products.get(product_id)
    if primary_product is None or primary_product.recommended_addon_id is None:
        return None

    addon_product = products.get(primary_product.recommended_addon_id)
    if addon_product is None:
        return None

    pitch = UpsellAgent().generate_pitch(
        primary_item_name=primary_product.name,
        addon_item_name=addon_product.name,
        addon_price=addon_product.base_price,
    )
    audit_record = AuditRecord(
        step="UPSELL_PITCH_GENERATED",
        action="GENERATE_CROSS_SELL_PITCH",
        status="SUCCESS",
        details=(
            f"Upsell Worker Agent generated a pitch for {addon_product.name} "
            f"(₹{addon_product.base_price:,})."
        ),
        timestamp=datetime.now(timezone.utc),
    )
    return UpsellDetails(
        pitch=pitch,
        item_id=addon_product.id,
        price=addon_product.base_price,
        audit_record=audit_record,
    )


def _extract_product_query_and_offer(prompt: str) -> tuple[str, int]:
    """Extract the product description and buyer offer from the prompt."""
    cleaned = prompt.strip()
    if not cleaned:
        raise ValueError("Prompt cannot be empty.")

    price_match = re.search(
        r"(?:₹|Rs\.?|INR)?\s*([\d,]+)",
        cleaned,
        flags=re.IGNORECASE,
    )
    offered_price = 0
    if price_match:
        offered_price = int(price_match.group(1).replace(",", ""))

    product_query = re.sub(
        r"\b(?:buy|purchase|get|need|looking for|want|for)\b",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    product_query = re.sub(
        r"(?:₹|Rs\.?|INR)?\s*[\d,]+",
        "",
        product_query,
        flags=re.IGNORECASE,
    )
    product_query = product_query.strip(" .,-:;!?")
    if not product_query:
        product_query = cleaned

    return product_query, offered_price


def _resolve_explicit_product_id(product_query: str) -> str | None:
    """Prefer explicit catalog product terms before falling back to vector similarity."""
    normalized = product_query.lower()
    explicit_terms = (
        (("gaming", "laptop"), "gaming_laptop"),
        (("laptop",), "laptop"),
        (("gaming", "console"), "gaming_console"),
        (("console",), "gaming_console"),
        (("mechanical", "keyboard"), "mechanical_keyboard_87keys"),
        (("keyboard",), "mechanical_keyboard_87keys"),
        (("ergonomic", "mouse"), "ergonomic_mouse"),
        (("mouse",), "ergonomic_mouse"),
        (("noise", "cancelling", "headphone"), "wireless_headphones"),
        (("headphone",), "wireless_headphones"),
    )
    for terms, product_id in explicit_terms:
        if all(term in normalized for term in terms):
            return product_id
    return None


@router.post(
    "/api/v1/semantic-negotiation",
    response_model=NegotiationResponse,
    summary="Resolve product intent and negotiate price with the seller agent",
)
def semantic_negotiation(request: NegotiationRequest) -> NegotiationResponse:
    """Use semantic search to resolve a product and negotiate pricing with strict seller guardrails."""
    try:
        if _is_incomplete_product_request(request.prompt):
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "product_id": "",
                    "offered_price": 0,
                    "negotiation": {
                        "agreed": False,
                        "final_price": 0,
                        "message_to_buyer": INCOMPLETE_PRODUCT_RESPONSE,
                    },
                    "audit": {
                        "step": "INTENT_CHECK",
                        "action": "REQUEST_PRODUCT_DETAILS",
                        "status": "PENDING",
                        "details": INCOMPLETE_PRODUCT_RESPONSE,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    "addon_accepted": False,
                    "traces": [
                        {
                            "step": "INTENT_CHECK",
                            "status": "pending",
                            "detail": INCOMPLETE_PRODUCT_RESPONSE,
                        }
                    ],
                },
            )
        if _is_out_of_domain(request.prompt):
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "product_id": "",
                    "offered_price": 0,
                    "negotiation": {
                        "agreed": False,
                        "final_price": 0,
                        "message_to_buyer": OUT_OF_DOMAIN_RESPONSE,
                    },
                    "audit": {
                        "step": "DOMAIN_GUARDRAIL",
                        "action": "REJECT_NON_COMMERCE_REQUEST",
                        "status": "BLOCKED",
                        "details": OUT_OF_DOMAIN_RESPONSE,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    "addon_accepted": False,
                    "traces": [
                        {
                            "step": "DOMAIN_GUARDRAIL",
                            "status": "blocked",
                            "detail": OUT_OF_DOMAIN_RESPONSE,
                        }
                    ],
                }
            )
        search_prompt = request.prompt
        is_confirmation = _is_confirmation(request.prompt)
        is_price_offer = _is_price_offer(request.prompt)
        reuse_active_context = (
            request.active_order is not None
            and bool(request.active_order.product_id)
            and (is_confirmation or is_price_offer)
        )
        if _addon_was_declined(request.prompt):
            previous_user_turns = [
                item["content"]
                for item in request.chat_history
                if item.get("role") == "user" and item.get("content")
            ]
            if previous_user_turns:
                search_prompt = previous_user_turns[-1]

        if reuse_active_context and request.active_order and request.active_order.product_id:
            product_id = request.active_order.product_id
            product_query = product_id
            offered_price = (
                _extract_product_query_and_offer(request.prompt)[1]
                if is_price_offer
                else request.active_order.total_amount or 0
            )
        else:
            product_query, offered_price = _extract_product_query_and_offer(search_prompt)
            product_id = _resolve_explicit_product_id(product_query)
            if product_id is None:
                semantic_catalog = SemanticCatalog()
                product_id = semantic_catalog.search(product_query)
        seller_agent = SellerAgent()
        negotiation = seller_agent.negotiate(
            product_id,
            offered_price,
            request.prompt,
            request.chat_history,
        )
        _, min_price, _ = seller_agent.get_product_constraints(product_id)
        active_order = ActiveOrderContext(
            product_id=product_id,
            total_amount=offered_price if offered_price > 0 else None,
        )
        has_price_offer = offered_price > 0
        minimum_price_passed = has_price_offer and offered_price >= min_price
        if minimum_price_passed:
            negotiation.agreed = True
            negotiation.final_price = offered_price

        audit = AuditRecord(
            step="NEGOTIATION",
            action="SEMANTIC_MATCH_AND_PRICE_CHECK",
            status="SUCCESS" if minimum_price_passed or not has_price_offer else "BLOCKED",
            details=(
                f"Resolved '{product_query}' to product_id '{product_id}' and negotiated final price "
                f"₹{negotiation.final_price}. Base price is negotiable; minimum price guardrail "
                f"{'passed' if minimum_price_passed else 'bypassed' if not has_price_offer else 'failed'}. "
                f"Seller message: {negotiation.message_to_buyer}"
            ),
            timestamp=datetime.now(timezone.utc),
        )

        if reuse_active_context:
            traces = [
                {
                    "step": "CONTEXT_REUSED",
                    "status": "success",
                    "detail": f"Active negotiation context reused for {product_id}; semantic search skipped.",
                },
                {
                    "step": "AGREEMENT_CONFIRMED",
                    "status": "success" if negotiation.agreed else "blocked",
                    "detail": negotiation.message_to_buyer,
                },
            ]
        else:
            traces = [
                {
                    "step": "Semantic Match",
                    "status": "success",
                    "detail": f"Semantic catalog matched '{product_query}' to {product_id}.",
                },
                {
                    "step": "Base Price Check",
                    "status": "success" if has_price_offer else "pending",
                    "detail": (
                        f"Buyer offer ₹{offered_price:,} was received."
                        if has_price_offer
                        else "No buyer offer provided; awaiting a price to negotiate."
                    ),
                },
                {
                    "step": "Min Price Check",
                    "status": "success" if minimum_price_passed or not has_price_offer else "blocked",
                    "detail": (
                        f"Offer cleared the seller floor at ₹{offered_price:,}."
                        if minimum_price_passed
                        else "Minimum price check bypassed until the buyer provides an offer."
                        if not has_price_offer
                        else negotiation.message_to_buyer
                    ),
                },
            ]

        order: CreateOrderResponse | None = None
        upsell: UpsellDetails | None = None
        if negotiation.agreed:
            order = _create_negotiated_order_response(product_id, negotiation.final_price)
            upsell = None if _addon_was_declined(request.prompt) else _create_upsell_details(product_id)

        return NegotiationResponse(
            success=negotiation.agreed,
            product_id=product_id,
            offered_price=offered_price,
            negotiation=negotiation.model_dump(),
            audit=audit,
            addon_accepted=bool(upsell),
            chat_history=request.chat_history,
            traces=traces,
            active_order=active_order,
            order=order if negotiation.agreed else None,
            upsell_pitch=upsell.pitch if negotiation.agreed and upsell else None,
            upsell_item_id=upsell.item_id if negotiation.agreed and upsell else None,
            upsell_price=upsell.price if negotiation.agreed and upsell else None,
            upsell_audit=upsell.audit_record if negotiation.agreed and upsell else None,
            provider_used=(seller_agent.last_benchmark or {}).get("provider_used"),
            model_used=(seller_agent.last_benchmark or {}).get("model_used"),
            latency_seconds=(seller_agent.last_benchmark or {}).get("latency_seconds"),
        )
    except (AgentExecutionError, ValueError, CatalogError, PaymentServiceError) as error:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": str(error),
                "error": "NEGOTIATION_FAILED",
            },
        )
    except HTTPException as error:
        return JSONResponse(
            status_code=error.status_code,
            content={
                "success": False,
                "message": error.detail,
                "error": "NEGOTIATION_FAILED",
            },
        )
    except Exception as error:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": f"Negotiation failed: {str(error)}",
                "error": "NEGOTIATION_FAILED",
            },
        )


@router.post(
    "/api/v1/checkout-combo",
    response_model=ComboCheckoutResponse,
    summary="Validate a negotiated bundle and generate a new Razorpay order",
)
def checkout_combo(request: ComboCheckoutRequest) -> ComboCheckoutResponse:
    """Enforce the dynamic combo floor and create a Razorpay order for the combined cart."""
    try:
        catalog = CatalogService()
        primary_product, primary_min_price = catalog.get_product_and_min_price(request.primary_product_id)
        upsell_product, upsell_min_price = catalog.get_product_and_min_price(request.upsell_product_id)

        combo_min_price = primary_min_price + upsell_min_price
        proposed_total = request.primary_agreed_price + upsell_product.price

        if proposed_total < combo_min_price:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Combo guardrail failed: proposed total ₹{proposed_total} is below the required "
                    f"minimum of ₹{combo_min_price}."
                ),
            )

        razorpay_client = PaymentService().client
        order_payload = RazorpayOrderRequest(
            amount=proposed_total * 100,
            currency="INR",
            notes={
                "primary_product_id": primary_product.id,
                "primary_agreed_price": str(request.primary_agreed_price),
                "upsell_product_id": upsell_product.id,
                "combo_total": str(proposed_total),
                "combo_min_price_verified": "true",
            },
        )
        response_data = razorpay_client.order.create(data=order_payload.model_dump())
        response = RazorpayOrderResponse.model_validate(response_data)
        payment_url = PaymentService().create_payment_link(
            amount=proposed_total,
            description=f"NexusPay combo checkout for {primary_product.name} + {upsell_product.name}",
            reference_id=response.id,
        )
        mandate = MandateService().generate_mandate(
            order_id=response.id,
            items=[
                {"product_id": primary_product.id, "quantity": 1},
                {"product_id": upsell_product.id, "quantity": 1},
            ],
            total_amount=proposed_total,
        )

        return ComboCheckoutResponse(
            success=True,
            order_id=response.id,
            total_amount=proposed_total,
            currency="INR",
            payment_url=payment_url,
            items=[
                {"name": primary_product.name, "price": request.primary_agreed_price},
                {"name": upsell_product.name, "price": upsell_product.price},
            ],
            message=(
                f"Combo checkout validated for {primary_product.name} + {upsell_product.name}. "
                f"New total: ₹{proposed_total:,}."
            ),
            intent_mandate=mandate,
        )
    except (CatalogError, PaymentServiceError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post(
    "/api/v1/create-order",
    response_model=CreateOrderResponse,
    summary="Create a server-verified Razorpay order for an agreed price",
)
def create_order(request: CreateOrderRequest) -> CreateOrderResponse:
    """Create a Razorpay Test Mode order after re-verifying the SQLite price floor."""
    try:
        return _create_negotiated_order_response(
            product_id=request.product_id,
            final_price=request.final_price,
            currency=request.currency,
        )
    except (CatalogError, PaymentServiceError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post(
    "/api/v1/agentic-checkout",
    response_model=CheckoutResponse,
    summary="Execute an agentic checkout",
)
def agentic_checkout(request: CheckoutRequest) -> CheckoutResponse:
    """Parse, validate, and optionally create a payment order."""
    try:
        agent = BuyerAgent()
        catalog = CatalogService()
        payment_service = PaymentService()
        intent = agent.process_user_intent(request.prompt)
        products = [catalog.get_product(item.product_id) for item in intent.items]
        guardrail_result = verify_order_intent(intent, products)

        if not guardrail_result.passed:
            audit = AuditRecord(
                step="GUARDRAIL",
                action="VERIFY_ORDER_INTENT",
                status="BLOCKED",
                details=guardrail_result.reason or "Order blocked by guardrail.",
                timestamp=datetime.now(timezone.utc),
            )
            return CheckoutResponse(
                success=False,
                intent=intent,
                guardrail_result=guardrail_result,
                payment_order=None,
                audit=audit,
                provider_used=agent.last_benchmark["provider_used"] if agent.last_benchmark else None,
                model_used=agent.last_benchmark["model_used"] if agent.last_benchmark else None,
                latency_seconds=agent.last_benchmark["latency_seconds"] if agent.last_benchmark else None,
            )

        payment_order, audit = payment_service.create_payment_order(
            intent,
            products,
            guardrail_result,
        )
        return CheckoutResponse(
            success=True,
            intent=intent,
            guardrail_result=guardrail_result,
            payment_order=payment_order,
            audit=audit,
            provider_used=agent.last_benchmark["provider_used"] if agent.last_benchmark else None,
            model_used=agent.last_benchmark["model_used"] if agent.last_benchmark else None,
            latency_seconds=agent.last_benchmark["latency_seconds"] if agent.last_benchmark else None,
        )
    except (AgentExecutionError, CatalogError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
