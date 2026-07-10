from django.contrib import admin

from .models import CustomerProfile


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "city", "country", "updated_at")
    search_fields = ("user__username", "user__email", "phone", "city")
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at", "updated_at")
