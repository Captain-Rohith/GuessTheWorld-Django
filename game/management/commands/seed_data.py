from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from game.models import Word
from accounts.models import UserRole

INITIAL_WORDS = [
    "APPLE", "BRAVE", "CRANE", "DRIVE", "EAGLE",
    "FLAME", "GRACE", "HOUSE", "LIGHT", "MANGO",
    "NOBLE", "OCEAN", "PIANO", "QUEEN", "RIVER",
    "SHINE", "TIGER", "UNITY", "VIPER", "WORLD"
]


def seed_initial_data(verbosity=1):
    User = get_user_model()

    # 1. Admin Account
    admin_user, admin_created = User.objects.get_or_create(
        username="AdminUser",
        defaults={
            "role": UserRole.ADMIN,
            "is_staff": True,
            "is_superuser": True,
        }
    )
    if admin_created:
        admin_user.set_password("AdminPassword1$")
        admin_user.save()
        if verbosity:
            print("Created AdminUser account.")
    else:
        admin_user.role = UserRole.ADMIN
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password("AdminPassword1$")
        admin_user.save()

    # 2. Player Account
    player_user, player_created = User.objects.get_or_create(
        username="PlayerOne",
        defaults={
            "role": UserRole.PLAYER,
            "is_staff": False,
            "is_superuser": False,
        }
    )
    if player_created:
        player_user.set_password("PlayerPassword1%")
        player_user.save()
        if verbosity:
            print("Created PlayerOne account.")
    else:
        player_user.role = UserRole.PLAYER
        player_user.is_staff = False
        player_user.is_superuser = False
        player_user.set_password("PlayerPassword1%")
        player_user.save()

    # 3. Seed 20 Words
    words_added = 0
    for w in INITIAL_WORDS:
        word_obj, created = Word.objects.get_or_create(word=w, defaults={"is_active": True})
        if created:
            words_added += 1

    if verbosity:
        print(f"Seeded {words_added} words into the database (Total: {Word.objects.count()}).")


class Command(BaseCommand):
    help = "Seeds the database with initial admin, player, and 20 five-letter words."

    def handle(self, *args, **options):
        seed_initial_data(verbosity=1)
        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully."))
