"""
Configuration de l'admin Django pour l'app fractionnement.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import CycleHebdomadaire, PeriodeConge, ParametresAnnee, CalculFractionnement


@admin.register(CycleHebdomadaire)
class CycleHebdomadaireAdmin(admin.ModelAdmin):
    """
    Administration des cycles hebdomadaires.
    """
    list_display = ['user', 'annee', 'heures_semaine', 'quotite_travail', 'rtt_annuels', 'conges_annuels', 'created_at']
    list_filter = ['annee', 'heures_semaine', 'quotite_travail', 'jours_ouvres_ou_ouvrables', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'annee']
    readonly_fields = ['rtt_annuels', 'conges_annuels', 'created_at', 'updated_at']
    ordering = ['-annee', 'user']
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('user', 'annee')
        }),
        (_('Cycle de travail'), {
            'fields': ('heures_semaine', 'quotite_travail', 'jours_ouvres_ou_ouvrables')
        }),
        (_('Calculs automatiques'), {
            'fields': ('rtt_annuels', 'conges_annuels'),
            'classes': ('collapse',)
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PeriodeConge)
class PeriodeCongeAdmin(admin.ModelAdmin):
    """
    Administration des périodes de congés.
    """
    list_display = ['user', 'date_debut', 'date_fin', 'type_conge', 'nb_jours', 'annee_civile', 'created_at']
    list_filter = ['type_conge', 'annee_civile', 'date_debut', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['annee_civile', 'nb_jours', 'created_at', 'updated_at']
    ordering = ['-date_debut', 'user']
    date_hierarchy = 'date_debut'
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('user', 'type_conge')
        }),
        (_('Période'), {
            'fields': ('date_debut', 'date_fin')
        }),
        (_('Calculs automatiques'), {
            'fields': ('annee_civile', 'nb_jours'),
            'classes': ('collapse',)
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ParametresAnnee)
class ParametresAnneeAdmin(admin.ModelAdmin):
    """
    Administration des paramètres d'année.
    """
    list_display = ['user', 'annee', 'jours_ouvres_ou_ouvrables', 'created_at']
    list_filter = ['annee', 'jours_ouvres_ou_ouvrables', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'annee']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-annee', 'user']
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('user', 'annee', 'jours_ouvres_ou_ouvrables')
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CalculFractionnement)
class CalculFractionnementAdmin(admin.ModelAdmin):
    """
    Administration des calculs de fractionnement.
    """
    list_display = ['user', 'annee', 'jours_hors_periode', 'jours_fractionnement', 'date_calcul']
    list_filter = ['annee', 'jours_fractionnement', 'date_calcul']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'annee']
    readonly_fields = ['jours_hors_periode', 'jours_fractionnement', 'date_calcul']
    ordering = ['-annee', 'user']
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('user', 'annee')
        }),
        (_('Résultats du calcul'), {
            'fields': ('jours_hors_periode', 'jours_fractionnement', 'date_calcul')
        }),
    )
