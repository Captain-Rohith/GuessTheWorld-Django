from django.test import TestCase
from django.core.exceptions import ValidationError
from accounts.models import CustomUser, UserRole
from accounts.validators import validate_custom_username, validate_custom_password
from accounts.forms import PlayerRegistrationForm, CustomLoginForm


class ValidatorTests(TestCase):
    def test_valid_username(self):
        # Must have at least 5 letters and contain both uppercase and lowercase characters
        valid_usernames = ["PlayerOne", "AdminUser", "UserA", "ValidUser123", "aBcDe"]
        for u in valid_usernames:
            try:
                validate_custom_username(u)
            except ValidationError:
                self.fail(f"validate_custom_username raised ValidationError unexpectedly for valid username '{u}'")

    def test_invalid_username_short(self):
        # Too short (< 5 characters)
        with self.assertRaises(ValidationError):
            validate_custom_username("Abc")

    def test_invalid_username_no_uppercase(self):
        # Missing uppercase
        with self.assertRaises(ValidationError):
            validate_custom_username("playerone")

    def test_invalid_username_no_lowercase(self):
        # Missing lowercase
        with self.assertRaises(ValidationError):
            validate_custom_username("PLAYERONE")

    def test_valid_password(self):
        # Must be >= 5 chars, contain alpha, numeric, and at least one from $, %, *, &
        valid_passwords = [
            "PlayerPassword1%",
            "AdminPassword1$",
            "Pass1*",
            "Secret9&",
            "Ab1$x"
        ]
        for p in valid_passwords:
            try:
                validate_custom_password(p)
            except ValidationError:
                self.fail(f"validate_custom_password raised ValidationError unexpectedly for valid password '{p}'")

    def test_invalid_password_short(self):
        with self.assertRaises(ValidationError):
            validate_custom_password("A1$")

    def test_invalid_password_no_alpha(self):
        with self.assertRaises(ValidationError):
            validate_custom_password("12345$")

    def test_invalid_password_no_numeric(self):
        with self.assertRaises(ValidationError):
            validate_custom_password("Abcde$")

    def test_invalid_password_no_special_char(self):
        with self.assertRaises(ValidationError):
            validate_custom_password("PlayerPass123")

    def test_invalid_password_disallowed_special_char(self):
        # Only $, %, *, & are allowed special chars
        with self.assertRaises(ValidationError):
            validate_custom_password("Player123@!")


class AccountsAuthViewsTests(TestCase):
    def test_player_registration_success(self):
        response = self.client.post("/register/", {
            "username": "NewPlayer",
            "password": "PlayerPass1$",
            "confirm_password": "PlayerPass1$",
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        user = CustomUser.objects.get(username="NewPlayer")
        self.assertEqual(user.role, UserRole.PLAYER)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_player_registration_password_mismatch(self):
        response = self.client.post("/register/", {
            "username": "NewPlayer2",
            "password": "PlayerPass1$",
            "confirm_password": "DifferentPass1$",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username="NewPlayer2").exists())

    def test_login_and_logout(self):
        # Pre-seeded PlayerOne
        response = self.client.post("/login/", {
            "username": "PlayerOne",
            "password": "PlayerPassword1%",
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user"].is_authenticated)

        # Logout
        logout_resp = self.client.get("/logout/", follow=True)
        self.assertEqual(logout_resp.status_code, 200)
        self.assertFalse(logout_resp.context["user"].is_authenticated)
