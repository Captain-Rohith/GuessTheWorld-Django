from django.apps import AppConfig
from django.db.models.signals import post_migrate


class GameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'game'

    def ready(self):
        from game.management.commands.seed_data import seed_initial_data

        def on_post_migrate(sender, **kwargs):
            # Only run when game app is migrated
            if sender.name == "game":
                seed_initial_data(verbosity=0)

        post_migrate.connect(on_post_migrate, sender=self)
