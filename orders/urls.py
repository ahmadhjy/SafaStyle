from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("cart/", views.cart_detail, name="cart"),
    path("cart/quick-add/", views.cart_quick_add, name="cart_quick_add"),
    path("cart/add/<int:variation_id>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:variation_id>/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:variation_id>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("order/<str:order_number>/", views.order_success, name="success"),
]
