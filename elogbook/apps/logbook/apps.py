from django.apps import AppConfig


class LogbookConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'elogbook.apps.logbook'
    
    def ready(self):
        import elogbook.apps.logbook.signals
