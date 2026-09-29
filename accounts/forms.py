from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, UserRole
from .validators import validate_custom_username, validate_custom_password


class PlayerRegistrationForm(forms.ModelForm):
    username = forms.CharField(
        label=_("Username"),
        max_length=150,
        validators=[validate_custom_username],
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "e.g. PlayerOne",
            "autocomplete": "username",
            "id": "id_username"
        }),
        help_text=_("Must be at least 5 characters and contain both uppercase (A-Z) and lowercase (a-z) letters.")
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={
            "class": "form-input password-field",
            "placeholder": "e.g. PlayerPassword1%",
            "autocomplete": "new-password",
            "id": "id_password"
        }),
        validators=[validate_custom_password],
        help_text=_("Must be at least 5 characters long, with letters, numbers, and at least one special character: $, %, *, &.")
    )
    confirm_password = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput(attrs={
            "class": "form-input password-field",
            "placeholder": "Re-enter password",
            "autocomplete": "new-password",
            "id": "id_confirm_password"
        })
    )

    class Meta:
        model = CustomUser
        fields = ["username"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", _("Passwords do not match."))

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = UserRole.PLAYER
        user.is_staff = False
        user.is_superuser = False
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class CustomLoginForm(forms.Form):
    username = forms.CharField(
        label=_("Username"),
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "Enter your username",
            "autocomplete": "username",
            "id": "id_login_username"
        })
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={
            "class": "form-input password-field",
            "placeholder": "Enter your password",
            "autocomplete": "current-password",
            "id": "id_login_password"
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    _("Invalid username or password. Please check your credentials and try again."),
                    code="invalid_login"
                )
            elif not self.user_cache.is_active:
                raise forms.ValidationError(
                    _("This account is currently inactive."),
                    code="inactive"
                )
        return self.cleaned_data

    def get_user(self):
        return self.user_cache
