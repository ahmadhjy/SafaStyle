from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.home, name="home"),
    path("shop/", views.shop, name="shop"),
    path("category/<slug:slug>/", views.category_detail, name="category"),
    path("product/<slug:slug>/", views.product_detail, name="product"),
    path("api/variation/<int:product_id>/", views.variation_api, name="variation_api"),
    path("api/quick-view/<slug:slug>/", views.quick_view, name="quick_view"),
]
