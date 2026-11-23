from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'elogbook.apps.notifications'
    label = 'notifications' 

    def ready(self):
        # Import signals for side effects
        try:
            import elogbook.apps.notifications.signals  # noqa: F401
        except Exception:
            # Do not crash if email not configured
            pass
