from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from .validators import validate_custom_username


class UserRole(models.TextChoices):
    ADMIN = "ADMIN", _("ADMIN")
    PLAYER = "PLAYER", _("PLAYER")


class CustomUser(AbstractUser):
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. Must have at least 5 characters and contain both uppercase and lowercase letters."
        ),
        validators=[validate_custom_username],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    role = models.CharField(
        max_length=10,
        choices=UserRole.choices,
        default=UserRole.PLAYER,
    )

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN or self.is_superuser or self.is_staff

    @property
    def is_player(self):
        return self.role == UserRole.PLAYER

    def __str__(self):
        return f"{self.username} ({self.role})"
