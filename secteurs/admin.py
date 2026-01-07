"""
Configuration de l'admin Django pour l'application secteurs.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Secteur


@admin.register(Secteur)
class SecteurAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour le modèle Secteur.
    """
    list_display = ['nom', 'couleur', 'ordre', 'created_at', 'get_user_count']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['nom']
    ordering = ['ordre', 'nom']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('nom', 'couleur', 'ordre')
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
        Retourne le nombre d'utilisateurs associés au secteur.

        Args:
            obj: Instance du secteur

        Returns:
            int: Nombre d'utilisateurs
        """
        return obj.utilisateurs.count()

    get_user_count.short_description = _('Nombre d\'utilisateurs')
    get_user_count.admin_order_field = 'utilisateurs__count'

