from django import forms

from .countries import COUNTRY_CHOICES
from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "first_name",
            "last_name",
            "company",
            "country",
            "street_address",
            "apartment",
            "city",
            "postcode",
            "phone",
            "email",
            "order_notes",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "First name", "required": True}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last name", "required": True}),
            "company": forms.TextInput(attrs={"placeholder": "Company name (optional)"}),
            "country": forms.Select(choices=COUNTRY_CHOICES),
            "street_address": forms.TextInput(
                attrs={"placeholder": "House number and street name"}
            ),
            "apartment": forms.TextInput(
                attrs={"placeholder": "Apartment, suite, unit, etc. (optional)"}
            ),
            "city": forms.TextInput(attrs={"placeholder": "Town / City"}),
            "postcode": forms.TextInput(attrs={"placeholder": "Postcode / ZIP (optional)"}),
            "phone": forms.TextInput(attrs={"placeholder": "Phone", "required": True}),
            "email": forms.EmailInput(attrs={"placeholder": "Email address (optional)"}),
            "order_notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Notes about your order, e.g. special notes for delivery.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["street_address"].required = True
        self.fields["city"].required = True
        self.fields["phone"].required = True
        self.fields["email"].required = False
        self.fields["company"].required = False
        self.fields["apartment"].required = False
        self.fields["postcode"].required = False
        self.fields["order_notes"].required = False
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "field-input")
            if field.required:
                field.widget.attrs["required"] = True
