from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        """Инициализация приложения"""
        # Импортируем сигналы
        try:
            import core.signals
        except ImportError:
            pass