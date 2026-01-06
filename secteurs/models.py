"""
Modèles de l'application secteurs.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class Secteur(models.Model):
    """
    Modèle représentant un secteur d'activité.
    """
    nom = models.CharField(
        _('nom'),
        max_length=200,
        unique=True,
        db_index=True,
        help_text=_('Nom du secteur d\'activité')
    )
    couleur = models.CharField(
        _('couleur'),
        max_length=7,
        help_text=_('Code couleur hexadécimal (ex: #1f4d9b)')
    )
    ordre = models.PositiveIntegerField(
        _('ordre'),
        default=0,
        db_index=True,
        help_text=_('Ordre d\'affichage du secteur')
    )
    created_at = models.DateTimeField(
        _('date de création'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('date de modification'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('secteur')
        verbose_name_plural = _('secteurs')
        ordering = ['ordre', 'nom']
        indexes = [
            models.Index(fields=['nom']),
            models.Index(fields=['ordre']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self) -> str:
        """
        Retourne la représentation string du secteur.

        Returns:
            str: Nom du secteur
        """
        return self.nom












