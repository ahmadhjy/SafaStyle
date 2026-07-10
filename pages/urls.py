from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("page/<slug:slug>/", views.page_detail, name="page"),
    path("contact/", views.contact, name="contact"),
    path("find-us/", views.find_us, name="find_us"),
]
