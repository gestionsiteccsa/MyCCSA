"""
Configuration de l'admin Django pour l'application events.
"""
from django.contrib import admin
from .models import Event, EventFile, EventAddress


@admin.register(EventAddress)
class EventAddressAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour EventAddress.
    """
    list_display = ['ville', 'code_postal', 'pays']
    search_fields = ['ville', 'rue', 'code_postal']
    list_filter = ['pays']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour Event.
    """
    list_display = ['titre', 'date_debut', 'date_fin', 'lieu', 'createur', 'date_publication_avant_le']
    list_filter = ['date_debut', 'secteurs', 'createur', 'date_publication_avant_le']
    search_fields = ['titre', 'description', 'lieu']
    filter_horizontal = ['secteurs']
    readonly_fields = ['created_at', 'updated_at', 'couleur_calendrier']
    # Optimisation SQL : précharger les relations ForeignKey pour éviter N+1 queries
    list_select_related = ['createur', 'adresse']

    fieldsets = (
        ('Informations générales', {
            'fields': ('titre', 'description', 'lieu', 'adresse')
        }),
        ('Dates', {
            'fields': ('date_debut', 'date_fin', 'timezone', 'date_publication_avant_le')
        }),
        ('Secteurs et affichage', {
            'fields': ('secteurs', 'couleur_calendrier')
        }),
        ('Métadonnées', {
            'fields': ('createur', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EventFile)
class EventFileAdmin(admin.ModelAdmin):
    """
    Configuration de l'admin pour EventFile.
    """
    list_display = ['nom', 'event', 'type_fichier', 'taille', 'uploaded_at', 'ordre']
    list_filter = ['type_fichier', 'uploaded_at']
    search_fields = ['nom', 'event__titre']
    readonly_fields = ['uploaded_at', 'taille']
