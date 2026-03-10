from django.apps import AppConfig


class ProvidersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "providers"

    def ready(self):
        from providers.signals import register_preference_signals

        register_preference_signals()
