"""
Modèles de l'application home.
"""
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """
    Modèle abstrait avec champs created_at et updated_at.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']


# Exemple de modèle - à adapter selon les besoins métier
class ExampleModel(TimeStampedModel):
    """
    Modèle exemple pour démontrer la structure.
    """
    name = models.CharField(
        max_length=200,
        db_index=True,
        verbose_name="Nom"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Actif"
    )

    class Meta:
        verbose_name = "Exemple"
        verbose_name_plural = "Exemples"
        indexes = [
            models.Index(fields=['name', 'is_active']),
        ]

    def __str__(self) -> str:
        return self.name
