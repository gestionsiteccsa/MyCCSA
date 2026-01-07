"""
Configuration de l'admin Django pour l'application role.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour le modèle Role.
    """
    list_display = ['nom', 'niveau', 'created_at', 'get_user_count']
    list_filter = ['niveau', 'created_at']
    search_fields = ['nom']
    ordering = ['niveau', 'nom']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('nom', 'niveau')
        }),
        (
            _('Dates importantes'),
            {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }
        ),
    )

    def get_user_count(self, obj):
        """
        Retourne le nombre d'utilisateurs associés au rôle.

        Args:
            obj: Instance du rôle

        Returns:
            int: Nombre d'utilisateurs
        """
        return obj.utilisateurs.count()

    get_user_count.short_description = _('Nombre d\'utilisateurs')
    get_user_count.admin_order_field = 'utilisateurs__count'
