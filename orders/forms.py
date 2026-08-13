from django import forms

from .countries import COUNTRY_CHOICES
from .models import DeliveryLocality, Governorate, Order


class CheckoutForm(forms.ModelForm):
    locality = forms.ModelChoiceField(
        queryset=DeliveryLocality.objects.none(),
        required=False,
        widget=forms.HiddenInput(attrs={"data-locality-id": "1"}),
    )
    payment_method = forms.ChoiceField(
        choices=[(Order.PaymentMethod.COD, "Cash on delivery")],
        initial=Order.PaymentMethod.COD,
        widget=forms.RadioSelect,
        required=True,
    )

    class Meta:
        model = Order
        fields = [
            "first_name",
            "last_name",
            "company",
            "country",
            "governorate",
            "locality",
            "street_address",
            "apartment",
            "city",
            "postcode",
            "phone",
            "email",
            "order_notes",
            "payment_method",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "First name", "required": True}),
            "last_name": forms.TextInput(attrs={"placeholder": "Last name", "required": True}),
            "company": forms.TextInput(attrs={"placeholder": "Company name (optional)"}),
            "country": forms.Select(choices=COUNTRY_CHOICES),
            "governorate": forms.Select(
                attrs={"data-governorate-select": "1"}
            ),
            "street_address": forms.TextInput(
                attrs={"placeholder": "House number and street name"}
            ),
            "apartment": forms.TextInput(
                attrs={"placeholder": "Apartment, suite, unit, etc. (optional)"}
            ),
            "city": forms.TextInput(
                attrs={
                    "placeholder": "Town / City",
                    "data-city-input": "1",
                    "autocomplete": "address-level2",
                }
            ),
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

    def __init__(self, *args, allow_whish=False, **kwargs):
        self.allow_whish = allow_whish
        super().__init__(*args, **kwargs)
        self.fields["governorate"].queryset = Governorate.objects.filter(is_active=True)
        self.fields["governorate"].empty_label = "Select governorate"
        self.fields["governorate"].required = False

        self.fields["locality"].queryset = (
            DeliveryLocality.objects.filter(is_active=True, governorate__is_active=True)
            .select_related("governorate")
            .order_by("name")
        )
        self.fields["locality"].required = False

        choices = [(Order.PaymentMethod.COD, "Cash on delivery")]
        if allow_whish:
            choices.append((Order.PaymentMethod.WHISH, "Whish Pay (Lebanon)"))
        self.fields["payment_method"].choices = choices

        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["street_address"].required = True
        # City is required for non-Lebanon; for Lebanon it is filled from locality.
        self.fields["city"].required = False
        self.fields["phone"].required = True
        self.fields["email"].required = False
        self.fields["company"].required = False
        self.fields["apartment"].required = False
        self.fields["postcode"].required = False
        self.fields["order_notes"].required = False
        for name, field in self.fields.items():
            if name == "payment_method":
                continue
            field.widget.attrs.setdefault("class", "field-input")
            if field.required:
                field.widget.attrs["required"] = True

    def clean(self):
        cleaned = super().clean()
        country = (cleaned.get("country") or "").strip()
        locality = cleaned.get("locality")
        city = (cleaned.get("city") or "").strip()
        payment_method = cleaned.get("payment_method") or Order.PaymentMethod.COD

        if country == "Lebanon":
            if not locality:
                self.add_error(
                    "locality",
                    "Please select your town / city from the list.",
                )
            else:
                # Server-side lock: fee zone always follows the selected locality.
                # Clients cannot pick Beirut while living in Aaramoun / Aramol.
                cleaned["governorate"] = locality.governorate
                cleaned["city"] = locality.name
                cleaned["locality"] = locality
        else:
            cleaned["governorate"] = None
            cleaned["locality"] = None
            if not city:
                self.add_error("city", "Please enter your town / city.")
            else:
                cleaned["city"] = city

        if payment_method == Order.PaymentMethod.WHISH:
            if not self.allow_whish:
                self.add_error(
                    "payment_method",
                    "Whish Pay is not available for this account yet.",
                )
            elif country != "Lebanon":
                self.add_error(
                    "payment_method",
                    "Whish Pay is only available for deliveries in Lebanon.",
                )

        cleaned["payment_method"] = payment_method
        return cleaned
