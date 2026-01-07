"""
Modèles de l'application fractionnement.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal

from .constants import HEURES_SEMAINE_MIN, HEURES_SEMAINE_MAX, CONGES_ANNUELS_BASE

User = get_user_model()


class CycleHebdomadaire(models.Model):
    """
    Modèle représentant le cycle hebdomadaire de travail d'un agent.
    """
    JOURS_CHOICES = [
        ('ouvres', _('Jours ouvrés (lundi-vendredi)')),
        ('ouvrables', _('Jours ouvrables (lundi-samedi)')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cycles_hebdomadaires',
        verbose_name=_('utilisateur'),
        db_index=True,
        help_text=_('Agent concerné par ce cycle')
    )
    annee = models.IntegerField(
        _('année'),
        db_index=True,
        help_text=_('Année civile de référence')
    )
    heures_semaine = models.DecimalField(
        _('heures par semaine'),
        max_digits=4,
        decimal_places=2,
        help_text=_('Nombre d\'heures travaillées par semaine (ex: 35, 37, 38, 39)')
    )
    quotite_travail = models.DecimalField(
        _('quotité de travail'),
        max_digits=3,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text=_('Quotité de travail (0.5 pour mi-temps, 1.0 pour temps complet)')
    )
    jours_ouvres_ou_ouvrables = models.CharField(
        _('jours ouvrés ou ouvrables'),
        max_length=10,
        choices=JOURS_CHOICES,
        default='ouvres',
        help_text=_('Type de jours utilisés pour le calcul')
    )
    rtt_annuels = models.IntegerField(
        _('RTT annuels'),
        default=0,
        help_text=_('Nombre de RTT calculés automatiquement')
    )
    conges_annuels = models.DecimalField(
        _('congés annuels'),
        max_digits=5,
        decimal_places=2,
        default=CONGES_ANNUELS_BASE,
        help_text=_('Nombre de jours de congés annuels (proratisé selon quotité)')
    )
    created_at = models.DateTimeField(
        _('date de création'),
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(
        _('date de modification'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('cycle hebdomadaire')
        verbose_name_plural = _('cycles hebdomadaires')
        unique_together = [['user', 'annee']]
        ordering = ['-annee', 'user']
        indexes = [
            models.Index(fields=['user', 'annee']),
            models.Index(fields=['annee']),
        ]

    def clean(self):
        """
        Valide les données du cycle hebdomadaire.

        Raises:
            ValidationError: Si les données sont invalides
        """
        super().clean()

        if self.heures_semaine < HEURES_SEMAINE_MIN or self.heures_semaine > HEURES_SEMAINE_MAX:
            raise ValidationError({
                'heures_semaine': _(
                    'Les heures par semaine doivent être entre %(min)s et %(max)s.'
                ) % {'min': HEURES_SEMAINE_MIN, 'max': HEURES_SEMAINE_MAX}
            })

        if self.quotite_travail < Decimal('0.5') or self.quotite_travail > Decimal('1.0'):
            raise ValidationError({
                'quotite_travail': _('La quotité de travail doit être entre 0.5 et 1.0.')
            })

    def __str__(self) -> str:
        """
        Retourne la représentation string du cycle.

        Returns:
            str: Description du cycle
        """
        return f"{self.user.get_full_name() or self.user.email} - {self.annee} ({self.heures_semaine}h/sem)"


class ParametresAnnee(models.Model):
    """
    Modèle représentant les paramètres globaux d'une année pour un utilisateur.
    """
    JOURS_CHOICES = [
        ('ouvres', _('Jours ouvrés (lundi-vendredi)')),
        ('ouvrables', _('Jours ouvrables (lundi-samedi)')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='parametres_annees',
        verbose_name=_('utilisateur'),
        db_index=True,
        help_text=_('Agent concerné')
    )
    annee = models.IntegerField(
        _('année'),
        db_index=True,
        help_text=_('Année civile')
    )
    jours_ouvres_ou_ouvrables = models.CharField(
        _('jours ouvrés ou ouvrables'),
        max_length=10,
        choices=JOURS_CHOICES,
        default='ouvres',
        help_text=_('Type de jours utilisés pour les calculs de l\'année')
    )
    created_at = models.DateTimeField(
        _('date de création'),
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(
        _('date de modification'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('paramètres année')
        verbose_name_plural = _('paramètres années')
        unique_together = [['user', 'annee']]
        ordering = ['-annee', 'user']
        indexes = [
            models.Index(fields=['user', 'annee']),
        ]

    def __str__(self) -> str:
        """
        Retourne la représentation string des paramètres.

        Returns:
            str: Description des paramètres
        """
        return f"{self.user.get_full_name() or self.user.email} - {self.annee}"


class PeriodeConge(models.Model):
    """
    Modèle représentant une période de congés prise par un agent.
    """
    TYPE_CONGE_CHOICES = [
        ('annuel', _('Congés annuels')),
        ('rtt', _('RTT')),
        ('asa', _('ASA (Autorisation Spéciale d\'Absence)')),
        ('maladie', _('Congé maladie')),
        ('autre', _('Autre')),
    ]

    DEMI_JOURNEE_CHOICES = [
        ('matin', _('Matin')),
        ('apres_midi', _('Après-midi')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='periodes_conges',
        verbose_name=_('utilisateur'),
        db_index=True,
        help_text=_('Agent concerné')
    )
    date_debut = models.DateField(
        _('date de début'),
        db_index=True,
        help_text=_('Date de début de la période de congés')
    )
    debut_type = models.CharField(
        _('début de période'),
        max_length=10,
        choices=DEMI_JOURNEE_CHOICES,
        default='matin',
        help_text=_('La période commence le matin ou l\'après-midi')
    )
    date_fin = models.DateField(
        _('date de fin'),
        db_index=True,
        help_text=_('Date de fin de la période de congés')
    )
    fin_type = models.CharField(
        _('fin de période'),
        max_length=10,
        choices=DEMI_JOURNEE_CHOICES,
        default='apres_midi',
        help_text=_('La période finit le matin ou l\'après-midi')
    )
    type_conge = models.CharField(
        _('type de congé'),
        max_length=20,
        choices=TYPE_CONGE_CHOICES,
        default='annuel',
        db_index=True,
        help_text=_('Type de congé pris')
    )
    annee_civile = models.IntegerField(
        _('année civile'),
        db_index=True,
        help_text=_('Année civile de référence (calculée automatiquement)')
    )
    nb_jours = models.DecimalField(
        _('nombre de jours'),
        max_digits=4,
        decimal_places=1,
        default=Decimal('0.0'),
        help_text=_('Nombre de jours calculés automatiquement (peut être décimal)')
    )
    created_at = models.DateTimeField(
        _('date de création'),
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(
        _('date de modification'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('période de congé')
        verbose_name_plural = _('périodes de congés')
        ordering = ['-date_debut', 'user']
        indexes = [
            models.Index(fields=['user', 'annee_civile']),
            models.Index(fields=['date_debut', 'date_fin']),
            models.Index(fields=['type_conge']),
            models.Index(fields=['user', 'date_debut']),
            models.Index(fields=['user', 'annee_civile', 'type_conge']),
        ]

    def clean(self):
        """
        Valide les données de la période de congé.

        Raises:
            ValidationError: Si les données sont invalides
        """
        super().clean()

        if self.date_debut and self.date_fin and self.date_fin < self.date_debut:
            raise ValidationError({
                'date_fin': _('La date de fin doit être postérieure ou égale à la date de début.')
            })

    def __str__(self) -> str:
        """
        Retourne la représentation string de la période.

        Returns:
            str: Description de la période
        """
        return f"{self.user.get_full_name() or self.user.email} - {self.date_debut} au {self.date_fin} ({self.type_conge})"


class CalculFractionnement(models.Model):
    """
    Modèle stockant le résultat du calcul des jours de fractionnement par année.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='calculs_fractionnement',
        verbose_name=_('utilisateur'),
        db_index=True,
        help_text=_('Agent concerné')
    )
    annee = models.IntegerField(
        _('année'),
        db_index=True,
        help_text=_('Année civile de référence')
    )
    jours_hors_periode = models.IntegerField(
        _('jours hors période principale'),
        default=0,
        help_text=_('Nombre de jours de congés annuels pris hors période principale (1er nov - 30 avr)')
    )
    jours_fractionnement = models.IntegerField(
        _('jours de fractionnement'),
        default=0,
        help_text=_('Nombre de jours de fractionnement obtenus (0, 1 ou 2)')
    )
    date_calcul = models.DateTimeField(
        _('date de calcul'),
        auto_now_add=True,
        db_index=True,
        help_text=_('Date et heure du calcul')
    )

    class Meta:
        verbose_name = _('calcul de fractionnement')
        verbose_name_plural = _('calculs de fractionnement')
        unique_together = [['user', 'annee']]
        ordering = ['-annee', 'user']
        indexes = [
            models.Index(fields=['user', 'annee']),
            models.Index(fields=['annee']),
        ]

    def __str__(self) -> str:
        """
        Retourne la représentation string du calcul.

        Returns:
            str: Description du calcul
        """
        return f"{self.user.get_full_name() or self.user.email} - {self.annee} ({self.jours_fractionnement} jour(s))"
