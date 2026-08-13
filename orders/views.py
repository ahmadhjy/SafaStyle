import logging
import threading
import uuid
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from catalog.models import Product, ProductVariation

from .cart import Cart
from .emails import send_order_emails
from .forms import CheckoutForm
from .models import DeliveryLocality, Governorate, Order, OrderItem
from .payments import decrement_stock_for_order, reconcile_whish_payment
from .whish import WhishError, create_payment, whish_available_for

logger = logging.getLogger(__name__)

CHECKOUT_TOKEN_KEY = "checkout_token"


def _send_order_emails_async(order):
    """Send order emails off the request thread so checkout never hangs on SMTP."""

    def _worker():
        from django.db import connection

        try:
            send_order_emails(order)
        finally:
            connection.close()

    threading.Thread(target=_worker, daemon=True).start()


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _cart_json(cart, ok=True, message="", error=""):
    return JsonResponse(
        {
            "ok": ok,
            "message": message,
            "error": error,
            "cart_count": len(cart),
            "cart_total": float(cart.subtotal),
        },
        status=200 if ok else 400,
    )


def cart_detail(request):
    cart = Cart(request)
    return render(request, "orders/cart.html", {"cart": cart})


@require_POST
def cart_add(request, variation_id):
    cart = Cart(request)
    variation = get_object_or_404(
        ProductVariation.objects.select_related("product", "color", "size"),
        pk=variation_id,
        is_active=True,
    )
    qty = int(request.POST.get("quantity", 1) or 1)
    ok = cart.add(variation, quantity=qty)
    if _is_ajax(request):
        return _cart_json(
            cart,
            ok=ok,
            message=f"Added {variation.product.name} to your bag." if ok else "",
            error="" if ok else "This item is out of stock.",
        )
    if not ok:
        messages.error(request, "This variation is out of stock.")
    else:
        messages.success(request, f"Added {variation.product.name} to your bag.")
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
    if request.POST.get("checkout"):
        return redirect("orders:checkout")
    return redirect(next_url)


@require_POST
def cart_quick_add(request):
    """Add to bag straight from a product card / quick-view (AJAX).

    Resolves the variation from product + optional color/size so the storefront
    never needs to know internal variation IDs.
    """
    cart = Cart(request)
    product = get_object_or_404(Product, pk=request.POST.get("product_id"), is_active=True)
    color_id = request.POST.get("color_id") or None
    size_id = request.POST.get("size_id") or None
    qty = int(request.POST.get("quantity", 1) or 1)

    qs = product.variations.filter(is_active=True)
    if color_id:
        qs = qs.filter(color_id=color_id)
    elif product.available_colors.count() == 1:
        qs = qs.filter(color_id=product.available_colors.first().pk)
    if size_id:
        qs = qs.filter(size_id=size_id)
    elif product.available_sizes.count() == 1:
        qs = qs.filter(size_id=product.available_sizes.first().pk)
    variation = qs.first()

    if not variation:
        if product.available_sizes.exists() and not size_id:
            return _cart_json(
                cart, ok=False, error="Please select a size before adding to your bag."
            )
        if product.available_colors.exists() and not color_id:
            return _cart_json(
                cart, ok=False, error="Please select a color before adding to your bag."
            )
        return _cart_json(cart, ok=False, error="Please choose the available options.")
    ok = cart.add(variation, quantity=qty)
    return _cart_json(
        cart,
        ok=ok,
        message=f"Added {product.name} to your bag." if ok else "",
        error="" if ok else "This item is out of stock.",
    )


@require_POST
def cart_update(request, variation_id):
    cart = Cart(request)
    variation = get_object_or_404(ProductVariation, pk=variation_id)
    qty = int(request.POST.get("quantity", 1) or 1)
    if qty <= 0:
        cart.remove(variation_id)
    else:
        cart.add(variation, quantity=qty, replace=True)
    return redirect("orders:cart")


@require_POST
def cart_remove(request, variation_id):
    cart = Cart(request)
    cart.remove(variation_id)
    messages.info(request, "Item removed.")
    return redirect("orders:cart")


def _build_order_from_cart(form, cart, request, profile):
    order = form.save(commit=False)
    if request.user.is_authenticated:
        order.user = request.user
    order.subtotal = cart.subtotal
    delivery_fee = Decimal("0")
    if order.country == "Lebanon" and order.governorate:
        delivery_fee = order.governorate.delivery_fee
    else:
        order.governorate = None
    order.delivery_fee = delivery_fee
    order.total = cart.subtotal + delivery_fee
    order.payment_method = form.cleaned_data["payment_method"]
    if order.payment_method == Order.PaymentMethod.WHISH:
        order.payment_status = Order.PaymentStatus.AWAITING
        order.whish_external_id = uuid.uuid4().hex
    else:
        order.payment_status = Order.PaymentStatus.NOT_REQUIRED
        order.whish_external_id = ""
        order.whish_collect_url = ""
    order.save()
    if profile is not None:
        profile.update_from_order(order)
    for item in cart:
        OrderItem.objects.create(
            order=order,
            product_name=item["name"],
            variation_label=item.get("label", ""),
            sku=item.get("sku", ""),
            unit_price=item["price"],
            quantity=item["qty"],
            line_total=item["total"],
            variation=item.get("variation"),
        )
    return order


def checkout(request):
    cart = Cart(request)
    allow_whish = whish_available_for(request)

    profile = None
    if request.user.is_authenticated:
        from accounts.models import CustomerProfile

        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # Guard against duplicate submissions (double-click, impatient resubmit,
        # or refreshing the POST). Each rendered checkout form carries a one-time
        # token; once it's used we won't create a second order for it.
        submitted_token = request.POST.get("checkout_token", "")
        session_token = request.session.get(CHECKOUT_TOKEN_KEY)
        if not submitted_token or submitted_token != session_token:
            last = request.session.get("last_order_number")
            if last:
                return redirect("orders:success", order_number=last)
            messages.info(request, "This order was already submitted.")
            return redirect("catalog:shop")

        if len(cart) == 0:
            messages.warning(request, "Your bag is empty.")
            return redirect("catalog:shop")

        form = CheckoutForm(request.POST, allow_whish=allow_whish)
        if form.is_valid():
            # Consume the token immediately so a near-simultaneous second POST
            # can't create a twin order.
            request.session.pop(CHECKOUT_TOKEN_KEY, None)

            payment_method = form.cleaned_data["payment_method"]

            if payment_method == Order.PaymentMethod.WHISH:
                order = None
                try:
                    with transaction.atomic():
                        order = _build_order_from_cart(form, cart, request, profile)
                    collect_url = create_payment(order)
                    order.whish_collect_url = collect_url
                    order.save(update_fields=["whish_collect_url", "updated_at"])
                except WhishError as exc:
                    logger.warning("Whish create_payment failed: %s", exc)
                    if order and order.pk:
                        order.delete()
                    # Re-issue token so the customer can retry without a hard fail loop.
                    checkout_token = uuid.uuid4().hex
                    request.session[CHECKOUT_TOKEN_KEY] = checkout_token
                    messages.error(
                        request,
                        f"Whish Pay could not start checkout: {exc}. "
                        "Please try again or use cash on delivery.",
                    )
                    form = CheckoutForm(request.POST, allow_whish=allow_whish)
                    governorates = list(
                        Governorate.objects.filter(is_active=True).values(
                            "id", "name", "delivery_fee"
                        )
                    )
                    localities = list(
                        DeliveryLocality.objects.filter(
                            is_active=True, governorate__is_active=True
                        )
                        .order_by("name")
                        .values("id", "name", "governorate_id")
                    )
                    return render(
                        request,
                        "orders/checkout.html",
                        {
                            "form": form,
                            "cart": cart,
                            "governorates_json": governorates,
                            "localities_json": localities,
                            "checkout_token": checkout_token,
                            "allow_whish": allow_whish,
                        },
                    )

                cart.clear()
                request.session["last_order_number"] = order.order_number
                return redirect(collect_url)

            # Cash on delivery — create, deduct stock, email, thank-you.
            with transaction.atomic():
                order = _build_order_from_cart(form, cart, request, profile)
                decrement_stock_for_order(order)

            cart.clear()
            request.session["last_order_number"] = order.order_number
            _send_order_emails_async(order)
            return redirect("orders:success", order_number=order.order_number)
    else:
        if len(cart) == 0:
            messages.warning(request, "Your bag is empty.")
            return redirect("catalog:shop")
        initial = profile.checkout_initial() if profile is not None else None
        form = CheckoutForm(initial=initial, allow_whish=allow_whish)

    # Issue a fresh one-time token for this render.
    checkout_token = uuid.uuid4().hex
    request.session[CHECKOUT_TOKEN_KEY] = checkout_token

    governorates = list(
        Governorate.objects.filter(is_active=True).values("id", "name", "delivery_fee")
    )
    localities = list(
        DeliveryLocality.objects.filter(is_active=True, governorate__is_active=True)
        .order_by("name")
        .values("id", "name", "governorate_id")
    )

    return render(
        request,
        "orders/checkout.html",
        {
            "form": form,
            "cart": cart,
            "governorates_json": governorates,
            "localities_json": localities,
            "checkout_token": checkout_token,
            "allow_whish": allow_whish,
        },
    )


def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, "orders/success.html", {"order": order})


def _whish_order_from_callback(request):
    external_id = (request.GET.get("externalId") or "").strip()
    order_number = (request.GET.get("order") or "").strip()
    qs = Order.objects.filter(payment_method=Order.PaymentMethod.WHISH)
    if external_id:
        order = qs.filter(whish_external_id=external_id).first()
        if order:
            return order
    if order_number:
        return qs.filter(order_number=order_number).first()
    return None


@csrf_exempt
@require_GET
def whish_callback_success(request):
    """Whish server → us: payment attempt succeeded. Verify before fulfilling."""
    order = _whish_order_from_callback(request)
    if not order:
        logger.warning("Whish success callback for unknown order: %s", request.GET)
        return HttpResponse("unknown", status=404)
    try:
        reconcile_whish_payment(order)
    except WhishError:
        logger.exception("Whish success callback reconcile failed for %s", order.order_number)
    return HttpResponse("ok")


@csrf_exempt
@require_GET
def whish_callback_failure(request):
    """Whish server → us: one attempt failed; link may still be payable."""
    order = _whish_order_from_callback(request)
    if not order:
        logger.warning("Whish failure callback for unknown order: %s", request.GET)
        return HttpResponse("unknown", status=404)
    # Do not cancel — docs say failure leaves the link open. Just acknowledge.
    logger.info("Whish failure callback for %s (link may still be payable)", order.order_number)
    return HttpResponse("ok")


def whish_redirect_success(request, order_number):
    """Browser return after payer finishes successfully on Whish hosted page."""
    order = get_object_or_404(
        Order, order_number=order_number, payment_method=Order.PaymentMethod.WHISH
    )
    try:
        order, status = reconcile_whish_payment(order)
    except WhishError as exc:
        logger.warning("Whish success redirect reconcile failed: %s", exc)
        messages.warning(
            request,
            "We’re confirming your Whish payment. If it doesn’t show as paid shortly, contact us.",
        )
        return render(request, "orders/whish_pending.html", {"order": order})

    if status == "success" or order.payment_status == Order.PaymentStatus.PAID:
        request.session["last_order_number"] = order.order_number
        return redirect("orders:success", order_number=order.order_number)

    return render(
        request,
        "orders/whish_pending.html",
        {"order": order, "collect_status": status},
    )


def whish_redirect_failure(request, order_number):
    """Browser return after a failed attempt — customer can retry the same link."""
    order = get_object_or_404(
        Order, order_number=order_number, payment_method=Order.PaymentMethod.WHISH
    )
    try:
        order, status = reconcile_whish_payment(order)
    except WhishError:
        status = "pending"

    if status == "success" or order.payment_status == Order.PaymentStatus.PAID:
        return redirect("orders:success", order_number=order.order_number)

    return render(
        request,
        "orders/whish_failed.html",
        {"order": order, "collect_status": status},
    )
