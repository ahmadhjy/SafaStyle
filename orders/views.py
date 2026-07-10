from decimal import Decimal

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Product, ProductVariation

from .cart import Cart
from .emails import send_order_emails
from .forms import CheckoutForm
from .models import OrderItem


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
    if size_id:
        qs = qs.filter(size_id=size_id)
    variation = qs.first()

    if not variation:
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


def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Your bag is empty.")
        return redirect("catalog:shop")

    profile = None
    if request.user.is_authenticated:
        from accounts.models import CustomerProfile

        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            order.subtotal = cart.subtotal
            order.total = cart.subtotal
            order.payment_method = "cod"
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
                variation = item.get("variation")
                if variation and variation.stock >= item["qty"]:
                    variation.stock -= item["qty"]
                    variation.save(update_fields=["stock", "updated_at"])
            cart.clear()
            send_order_emails(order)
            return redirect("orders:success", order_number=order.order_number)
    else:
        initial = profile.checkout_initial() if profile is not None else None
        form = CheckoutForm(initial=initial)

    return render(
        request,
        "orders/checkout.html",
        {"form": form, "cart": cart},
    )


def order_success(request, order_number):
    from .models import Order

    order = get_object_or_404(Order, order_number=order_number)
    return render(request, "orders/success.html", {"order": order})
