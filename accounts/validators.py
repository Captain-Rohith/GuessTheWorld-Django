import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_custom_username(value):
    if not value or len(value) < 5:
        raise ValidationError(
            _("Username must have at least 5 characters."),
            code="username_too_short",
        )
    if not re.search(r"[A-Z]", value):
        raise ValidationError(
            _("Username must contain at least one uppercase letter (A-Z)."),
            code="username_no_uppercase",
        )
    if not re.search(r"[a-z]", value):
        raise ValidationError(
            _("Username must contain at least one lowercase letter (a-z)."),
            code="username_no_lowercase",
        )


def validate_custom_password(value):
    if not value or len(value) < 5:
        raise ValidationError(
            _("Password must be at least 5 characters long."),
            code="password_too_short",
        )
    if not re.search(r"[a-zA-Z]", value):
        raise ValidationError(
            _("Password must contain at least one alphabetic character (a-zA-Z)."),
            code="password_no_alpha",
        )
    if not re.search(r"[0-9]", value):
        raise ValidationError(
            _("Password must contain at least one numeric character (0-9)."),
            code="password_no_numeric",
        )
    if not re.search(r"[\$%*&]", value):
        raise ValidationError(
            _("Password must contain at least one special character from: $, %, *, &."),
            code="password_no_special",
        )


class CustomPasswordComplexityValidator:
    def validate(self, password, user=None):
        validate_custom_password(password)

    def get_help_text(self):
        return _(
            "Your password must be at least 5 characters long and contain alphabetic characters, numbers, and at least one special character from: $, %, *, &."
        )
