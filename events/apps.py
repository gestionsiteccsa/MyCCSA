"""
Configuration de l'application events.
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EventsConfig(AppConfig):
    """
    Configuration de l'application events.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'events'
    verbose_name = _('Événements')

    def ready(self):
        """
        Méthode appelée quand l'application est prête.
        """
        import events.signals  # noqa












