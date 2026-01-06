"""
Modèles de l'application role.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.Model):
    """
    Modèle représentant un rôle hiérarchique.
    """
    nom = models.CharField(
        _('nom'),
        max_length=200,
        unique=True,
        db_index=True,
        help_text=_('Nom du rôle hiérarchique')
    )
    niveau = models.PositiveIntegerField(
        _('niveau'),
        unique=True,
        db_index=True,
        help_text=_('Niveau hiérarchique (0 = agents, 1 = coordo, 2 = directeur, etc.)')
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
        verbose_name = _('rôle')
        verbose_name_plural = _('rôles')
        ordering = ['niveau', 'nom']
        indexes = [
            models.Index(fields=['nom']),
            models.Index(fields=['niveau']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self) -> str:
        """
        Retourne la représentation string du rôle.

        Returns:
            str: Nom du rôle
        """
        return self.nom









