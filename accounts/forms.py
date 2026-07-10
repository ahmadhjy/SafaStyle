from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)

from .models import CustomerProfile

User = get_user_model()

_INPUT = {"class": "field-input"}


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "field-input", "placeholder": "Username or email", "autofocus": True}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "field-input", "placeholder": "Password"}
        )


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs=_INPUT))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs=_INPUT))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs=_INPUT))

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "username")
        widgets = {"username": forms.TextInput(attrs=_INPUT)}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("password1", "password2"):
            self.fields[name].widget.attrs.update(_INPUT)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user


class StyledPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update(
            {"class": "field-input", "placeholder": "Email address", "autofocus": True}
        )


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(_INPUT)


class StyledSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(_INPUT)


class AccountDetailsForm(forms.Form):
    """Edit the shopper's name/email (User) + saved shipping info (profile)."""

    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs=_INPUT))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs=_INPUT))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs=_INPUT))
    phone = forms.CharField(max_length=40, required=False, widget=forms.TextInput(attrs=_INPUT))
    company = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs=_INPUT))
    country = forms.CharField(
        max_length=100, required=False, initial="Lebanon", widget=forms.TextInput(attrs=_INPUT)
    )
    street_address = forms.CharField(
        max_length=255, required=False, widget=forms.TextInput(attrs=_INPUT)
    )
    apartment = forms.CharField(
        max_length=255, required=False, widget=forms.TextInput(attrs=_INPUT)
    )
    city = forms.CharField(max_length=120, required=False, widget=forms.TextInput(attrs=_INPUT))
    postcode = forms.CharField(
        max_length=40, required=False, widget=forms.TextInput(attrs=_INPUT)
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def save(self):
        user = self.user
        data = self.cleaned_data
        user.first_name = data["first_name"]
        user.last_name = data["last_name"]
        user.email = data["email"]
        user.save(update_fields=["first_name", "last_name", "email"])
        profile, _ = CustomerProfile.objects.get_or_create(user=user)
        for field in (
            "phone",
            "company",
            "country",
            "street_address",
            "apartment",
            "city",
            "postcode",
        ):
            setattr(profile, field, data.get(field, ""))
        profile.save()
        return profile
