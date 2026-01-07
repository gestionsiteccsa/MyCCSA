"""
Configuration de l'application role.
"""
from django.apps import AppConfig


class RoleConfig(AppConfig):
    """
    Configuration de l'application role.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'role'
    verbose_name = 'Rôles'

