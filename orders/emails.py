import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_order_emails(order):
    """Send the customer confirmation and the store notification for an order.

    Failures are logged but never raised, so a mail hiccup can't break checkout.
    """
    items = list(order.items.all())
    ctx = {
        "order": order,
        "items": items,
        "store_name": "Safa Style",
        "notification_emails": settings.ORDER_NOTIFICATION_EMAILS,
    }

    # 1) Confirmation to the customer (only if they gave an email).
    if order.email:
        try:
            _send(
                subject=f"We received your order — {order.order_number}",
                text_template="emails/order_confirmation.txt",
                html_template="emails/order_confirmation.html",
                ctx=ctx,
                to=[order.email],
            )
        except Exception:  # pragma: no cover - defensive
            logger.exception("Failed to send order confirmation for %s", order.order_number)

    # 2) Notification to the store team.
    try:
        _send(
            subject=f"New order {order.order_number} — {order.full_name}",
            text_template="emails/order_notification.txt",
            html_template="emails/order_notification.html",
            ctx=ctx,
            to=settings.ORDER_NOTIFICATION_EMAILS,
            reply_to=[order.email] if order.email else None,
        )
    except Exception:  # pragma: no cover - defensive
        logger.exception("Failed to send order notification for %s", order.order_number)


def _send(subject, text_template, html_template, ctx, to, reply_to=None):
    text_body = render_to_string(text_template, ctx)
    html_body = render_to_string(html_template, ctx)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to,
        reply_to=reply_to,
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)
