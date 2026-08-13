"""Whish Pay API client (sandbox / production)."""

from __future__ import annotations

import logging
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


class WhishError(Exception):
    def __init__(self, message, code=None, payload=None):
        super().__init__(message)
        self.code = code
        self.payload = payload or {}


def whish_configured():
    return bool(
        settings.WHISH_PAY_ENABLED
        and settings.WHISH_CHANNEL
        and settings.WHISH_SECRET
        and settings.WHISH_WEBSITE_URL
    )


def whish_available_for(request):
    """Whether the current user may see / use Whish Pay at checkout."""
    if not whish_configured():
        return False
    if settings.WHISH_PAY_ADMIN_ONLY:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated or not user.is_staff:
            return False
    return True


def _headers():
    return {
        "channel": settings.WHISH_CHANNEL,
        "secret": settings.WHISH_SECRET,
        "websiteUrl": settings.WHISH_WEBSITE_URL,
        "User-Agent": settings.WHISH_USER_AGENT,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _url(path):
    return f"{settings.WHISH_API_BASE.rstrip('/')}/{path.lstrip('/')}"


def _request(method, path, *, json_body=None, params=None):
    try:
        resp = requests.request(
            method,
            _url(path),
            headers=_headers(),
            json=json_body,
            params=params,
            timeout=settings.WHISH_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.exception("Whish API network error: %s %s", method, path)
        raise WhishError(f"Could not reach Whish Pay: {exc}") from exc

    try:
        payload = resp.json()
    except ValueError as exc:
        logger.error("Whish API non-JSON response (%s): %s", resp.status_code, resp.text[:500])
        raise WhishError("Unexpected response from Whish Pay.") from exc

    # Docs: always branch on body status/code, not HTTP status.
    if payload.get("status") is True:
        return payload

    code = payload.get("code")
    if code == "500" or code == 500:
        raise WhishError(
            "Whish Pay is still processing this request. Please check status shortly.",
            code="500",
            payload=payload,
        )

    dialog = payload.get("dialog") or {}
    message = dialog.get("message") or dialog.get("title") or "Whish Pay request failed."
    raise WhishError(message, code=str(code) if code is not None else None, payload=payload)


def format_amount_usd(amount: Decimal) -> str:
    quantized = Decimal(amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if quantized < Decimal("1.00"):
        raise WhishError("Whish Pay requires a minimum of $1.00 USD.")
    return f"{quantized:.2f}"


def absolute_url(path: str) -> str:
    return f"{settings.SITE_URL.rstrip('/')}{path}"


def callback_urls(order):
    """Build public callback + redirect URLs with our own reference params."""
    qs = urlencode(
        {"externalId": order.whish_external_id, "order": order.order_number}
    )
    return {
        "successCallbackUrl": absolute_url(
            reverse("orders:whish_callback_success") + f"?{qs}"
        ),
        "failureCallbackUrl": absolute_url(
            reverse("orders:whish_callback_failure") + f"?{qs}"
        ),
        "successRedirectUrl": absolute_url(
            reverse("orders:whish_redirect_success", args=[order.order_number])
        ),
        "failureRedirectUrl": absolute_url(
            reverse("orders:whish_redirect_failure", args=[order.order_number])
        ),
    }


def create_payment(order):
    """Create a hosted Whish payment link for an order. Returns collectUrl."""
    body = {
        "amount": format_amount_usd(order.total),
        "currency": settings.WHISH_CURRENCY,
        "invoice": f"Order {order.order_number}",
        "externalId": str(order.whish_external_id),
        **callback_urls(order),
    }
    payload = _request("POST", "/payment/whish", json_body=body)
    data = payload.get("data") or {}
    collect_url = data.get("collectUrl")
    if not collect_url:
        raise WhishError("Whish Pay did not return a payment link.", payload=payload)
    return collect_url


def get_payment_status(external_id, currency=None):
    currency = currency or settings.WHISH_CURRENCY
    payload = _request(
        "POST",
        "/payment/collect/status",
        json_body={"currency": currency, "externalId": str(external_id)},
    )
    data = payload.get("data") or {}
    return {
        "collect_status": data.get("collectStatus"),
        "payer_phone": data.get("payerPhoneNumber") or "",
        "raw": payload,
    }
