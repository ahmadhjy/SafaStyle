from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from orders.models import Order

from .forms import AccountDetailsForm, SignUpForm
from .models import CustomerProfile


def signup(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to Safa Style! Your account is ready.")
            return redirect(request.GET.get("next") or "accounts:dashboard")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


def _user_orders(user):
    """Orders linked to the account, plus any guest orders with the same email."""
    qs = Order.objects.filter(user=user)
    if user.email:
        qs = qs | Order.objects.filter(user__isnull=True, email__iexact=user.email)
    return qs.distinct().order_by("-created_at")


@login_required
def dashboard(request):
    orders = _user_orders(request.user)
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    return render(
        request,
        "accounts/dashboard.html",
        {
            "recent_orders": orders[:5],
            "order_count": orders.count(),
            "profile": profile,
        },
    )


@login_required
def order_history(request):
    return render(
        request,
        "accounts/orders.html",
        {"orders": _user_orders(request.user)},
    )


@login_required
def order_detail(request, order_number):
    orders = _user_orders(request.user)
    order = get_object_or_404(orders, order_number=order_number)
    return render(request, "accounts/order_detail.html", {"order": order})


@login_required
def account_details(request):
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = AccountDetailsForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your details have been saved.")
            return redirect("accounts:details")
    else:
        initial = profile.checkout_initial()
        form = AccountDetailsForm(initial=initial, user=request.user)
    return render(request, "accounts/details.html", {"form": form})
