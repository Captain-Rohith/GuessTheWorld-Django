from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def validate_five_letter_word(value):
    if not value or len(value) != 5 or not value.isalpha():
        raise ValidationError(
            _("Word must consist of exactly 5 alphabetic letters."),
            code="invalid_word_format",
        )


class Word(models.Model):
    word = models.CharField(
        max_length=5,
        unique=True,
        validators=[validate_five_letter_word],
        help_text=_("5-letter uppercase English word"),
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Designates whether this word is available for active gameplay."),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["word"]

    def clean(self):
        super().clean()
        if self.word:
            self.word = self.word.strip().upper()
            validate_five_letter_word(self.word)

    def save(self, *args, **kwargs):
        if self.word:
            self.word = self.word.strip().upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.word} ({'Active' if self.is_active else 'Inactive'})"


class GameStatus(models.TextChoices):
    IN_PROGRESS = "IN_PROGRESS", _("IN_PROGRESS")
    WON = "WON", _("WON")
    LOST = "LOST", _("LOST")


class GameSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="game_sessions",
    )
    target_word = models.CharField(max_length=5)
    max_attempts = models.IntegerField(default=5)
    attempts_used = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=GameStatus.choices,
        default=GameStatus.IN_PROGRESS,
    )
    session_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Game {self.id} - {self.user.username} - {self.status}"


class GuessAttempt(models.Model):
    game_session = models.ForeignKey(
        GameSession,
        on_delete=models.CASCADE,
        related_name="guesses",
    )
    attempt_number = models.IntegerField()
    guess_word = models.CharField(max_length=5)
    guessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["attempt_number"]

    def __str__(self):
        return f"Attempt {self.attempt_number}: {self.guess_word} for Session {self.game_session_id}"
