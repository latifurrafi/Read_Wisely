from django.apps import AppConfig


class ReldemoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reldemo'

    # def ready(self):
    #     import reldemo.signals  # Ensure signals are loaded


