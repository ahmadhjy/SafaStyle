"""Shared payment fulfillment helpers (Whish Pay, etc.)."""

from __future__ import annotations

import logging
import threading

from django.db import transaction
from django.utils import timezone

from .emails import send_order_emails
from .models import Order
from .whish import WhishError, get_payment_status

logger = logging.getLogger(__name__)


def decrement_stock_for_order(order):
    for item in order.items.select_related("variation"):
        variation = item.variation
        if variation and variation.stock >= item.quantity:
            variation.stock -= item.quantity
            variation.save(update_fields=["stock", "updated_at"])


def _send_emails_async(order):
    def _worker():
        from django.db import connection

        try:
            send_order_emails(order)
        finally:
            connection.close()

    threading.Thread(target=_worker, daemon=True).start()


def mark_whish_order_paid(order, *, payer_phone=""):
    """Idempotently mark a Whish order paid, decrement stock, send emails."""
    if order.payment_method != Order.PaymentMethod.WHISH:
        return order, False

    with transaction.atomic():
        locked = Order.objects.select_for_update().get(pk=order.pk)
        if locked.payment_status == Order.PaymentStatus.PAID:
            return locked, False

        locked.payment_status = Order.PaymentStatus.PAID
        locked.status = Order.Status.CONFIRMED
        locked.paid_at = timezone.now()
        if payer_phone:
            locked.whish_payer_phone = payer_phone
        locked.save(
            update_fields=[
                "payment_status",
                "status",
                "paid_at",
                "whish_payer_phone",
                "updated_at",
            ]
        )
        decrement_stock_for_order(locked)

    _send_emails_async(locked)
    return locked, True


def reconcile_whish_payment(order):
    """Ask Whish for status and update the order. Returns (order, collect_status)."""
    if not order.whish_external_id:
        raise WhishError("Order has no Whish payment reference.")

    result = get_payment_status(order.whish_external_id)
    status = (result.get("collect_status") or "").lower()
    payer = result.get("payer_phone") or ""

    if status == "success":
        order, _ = mark_whish_order_paid(order, payer_phone=payer)
    elif status == "failed":
        Order.objects.filter(pk=order.pk).exclude(
            payment_status=Order.PaymentStatus.PAID
        ).update(
            payment_status=Order.PaymentStatus.FAILED,
            updated_at=timezone.now(),
        )
        order.refresh_from_db()
    elif status == "refunded":
        Order.objects.filter(pk=order.pk).update(
            payment_status=Order.PaymentStatus.REFUNDED,
            updated_at=timezone.now(),
        )
        order.refresh_from_db()

    return order, status
