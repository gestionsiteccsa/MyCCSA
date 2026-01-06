"""
Formulaires de l'application fractionnement.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from decimal import Decimal

from .models import CycleHebdomadaire, PeriodeConge, ParametresAnnee
from .constants import (
    ANNEE_MIN,
    ANNEE_MAX,
    HEURES_SEMAINE_MIN,
    HEURES_SEMAINE_MAX,
    QUOTITE_TRAVAIL_MIN,
    QUOTITE_TRAVAIL_MAX,
    PAGINATION_PAR_PAGE,
)
from .services.calcul_service import (
    calculer_rtt_annuels,
    calculer_conges_annuels,
    compter_jours_periode,
)
from .utils import est_dans_periode_principale

User = get_user_model()


class CycleHebdomadaireForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier un cycle hebdomadaire.
    """
    class Meta:
        model = CycleHebdomadaire
        fields = ['annee', 'heures_semaine', 'quotite_travail', 'jours_ouvres_ou_ouvrables']
        widgets = {
            'annee': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'min': ANNEE_MIN,
                'max': ANNEE_MAX,
            }),
            'heures_semaine': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'step': '0.5',
                'min': str(HEURES_SEMAINE_MIN),
                'max': str(HEURES_SEMAINE_MAX),
            }),
            'quotite_travail': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'step': '0.1',
                'min': str(QUOTITE_TRAVAIL_MIN),
                'max': str(QUOTITE_TRAVAIL_MAX),
            }),
            'jours_ouvres_ou_ouvrables': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
            }),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialise le formulaire.

        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés (peut contenir 'user')
        """
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pré-remplir l'année avec l'année courante si nouveau cycle
        if not self.instance.pk:
            from datetime import date
            self.fields['annee'].initial = date.today().year

    def clean_annee(self):
        """
        Valide l'année.

        Returns:
            int: Année validée

        Raises:
            ValidationError: Si l'année est invalide
        """
        annee = self.cleaned_data.get('annee')
        
        if annee < ANNEE_MIN or annee > ANNEE_MAX:
            raise ValidationError(
                _('L\'année doit être entre %(min)s et %(max)s.') % {
                    'min': ANNEE_MIN,
                    'max': ANNEE_MAX
                }
            )
        
        # Vérifier qu'il n'existe pas déjà un cycle pour cet utilisateur et cette année
        if self.user:
            existing = CycleHebdomadaire.objects.filter(
                user=self.user,
                annee=annee
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    _('Un cycle existe déjà pour l\'année %(annee)s.') % {'annee': annee}
                )
        
        return annee

    def clean_heures_semaine(self):
        """
        Valide les heures par semaine.

        Returns:
            Decimal: Heures validées

        Raises:
            ValidationError: Si les heures sont invalides
        """
        heures_semaine = self.cleaned_data.get('heures_semaine')
        
        if heures_semaine < HEURES_SEMAINE_MIN or heures_semaine > HEURES_SEMAINE_MAX:
            raise ValidationError(
                _('Les heures par semaine doivent être entre %(min)s et %(max)s.') % {
                    'min': HEURES_SEMAINE_MIN,
                    'max': HEURES_SEMAINE_MAX
                }
            )
        
        return heures_semaine

    def clean_quotite_travail(self):
        """
        Valide la quotité de travail.

        Returns:
            Decimal: Quotité validée

        Raises:
            ValidationError: Si la quotité est invalide
        """
        quotite = self.cleaned_data.get('quotite_travail')
        
        if quotite < QUOTITE_TRAVAIL_MIN or quotite > QUOTITE_TRAVAIL_MAX:
            raise ValidationError(
                _('La quotité de travail doit être entre %(min)s et %(max)s.') % {
                    'min': QUOTITE_TRAVAIL_MIN,
                    'max': QUOTITE_TRAVAIL_MAX
                }
            )
        
        return quotite

    def clean(self):
        """
        Valide le formulaire et calcule automatiquement RTT et CA.

        Returns:
            dict: Données nettoyées

        Raises:
            ValidationError: Si les données sont invalides
        """
        cleaned_data = super().clean()
        
        heures_semaine = cleaned_data.get('heures_semaine')
        quotite_travail = cleaned_data.get('quotite_travail')
        jours_ouvres_ou_ouvrables = cleaned_data.get('jours_ouvres_ou_ouvrables', 'ouvres')
        
        if heures_semaine and quotite_travail:
            # Calculer automatiquement RTT et CA
            rtt = calculer_rtt_annuels(heures_semaine, quotite_travail)
            ca = calculer_conges_annuels(quotite_travail, jours_ouvres_ou_ouvrables)
            
            # Stocker les valeurs calculées (seront utilisées dans save())
            self.rtt_calcule = rtt
            self.ca_calcule = ca
        
        return cleaned_data

    def save(self, commit=True):
        """
        Sauvegarde le cycle avec les calculs automatiques.

        Args:
            commit: Si True, sauvegarde en base de données

        Returns:
            CycleHebdomadaire: Instance du cycle sauvegardé
        """
        instance = super().save(commit=False)
        
        if self.user:
            instance.user = self.user
        
        # Appliquer les calculs automatiques
        if hasattr(self, 'rtt_calcule'):
            instance.rtt_annuels = self.rtt_calcule
        if hasattr(self, 'ca_calcule'):
            instance.conges_annuels = self.ca_calcule
        
        if commit:
            instance.save()
        
        return instance


class PeriodeCongeForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier une période de congé.
    """
    class Meta:
        model = PeriodeConge
        fields = ['date_debut', 'debut_type', 'date_fin', 'fin_type', 'type_conge']
        widgets = {
            'date_debut': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'type': 'date',
            }),
            'debut_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
            }),
            'date_fin': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'type': 'date',
            }),
            'fin_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
            }),
            'type_conge': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
            }),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialise le formulaire.

        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés (peut contenir 'user')
        """
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_date_fin(self):
        """
        Valide que date_fin >= date_debut.

        Returns:
            date: Date de fin validée

        Raises:
            ValidationError: Si date_fin < date_debut
        """
        date_debut = self.cleaned_data.get('date_debut')
        date_fin = self.cleaned_data.get('date_fin')
        
        if date_fin and date_debut and date_fin < date_debut:
            raise ValidationError(
                _('La date de fin doit être postérieure ou égale à la date de début.')
            )
        
        return date_fin

    def clean(self):
        """
        Valide le formulaire et calcule automatiquement annee_civile et nb_jours.

        Returns:
            dict: Données nettoyées

        Raises:
            ValidationError: Si les données sont invalides
        """
        cleaned_data = super().clean()
        
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        debut_type = cleaned_data.get('debut_type', 'matin')
        fin_type = cleaned_data.get('fin_type', 'apres_midi')
        
        if date_debut and date_fin:
            # Calculer l'année civile (année de la date de début)
            annee_civile = date_debut.year
            
            # Récupérer les paramètres pour savoir si on compte jours orvrés ou ouvrables
            jours_type = 'ouvres'  # Par défaut
            if self.user:
                try:
                    parametres = ParametresAnnee.objects.get(user=self.user, annee=annee_civile)
                    jours_type = parametres.jours_ouvres_ou_ouvrables
                except ParametresAnnee.DoesNotExist:
                    # Essayer de récupérer depuis le cycle hebdomadaire
                    try:
                        cycle = CycleHebdomadaire.objects.get(user=self.user, annee=annee_civile)
                        jours_type = cycle.jours_ouvres_ou_ouvrables
                    except CycleHebdomadaire.DoesNotExist:
                        pass
            
            # Compter les jours
            nb_jours = compter_jours_periode(
                date_debut,
                date_fin,
                jours_type,
                exclure_feries=True,
                annee=annee_civile,
                debut_type=debut_type,
                fin_type=fin_type
            )
            
            # Stocker les valeurs calculées
            self.annee_civile_calculee = annee_civile
            self.nb_jours_calcule = nb_jours
        
        return cleaned_data

    def save(self, commit=True):
        """
        Sauvegarde la période avec les calculs automatiques.

        Args:
            commit: Si True, sauvegarde en base de données

        Returns:
            PeriodeConge: Instance de la période sauvegardée
        """
        instance = super().save(commit=False)
        
        if self.user:
            instance.user = self.user
        
        # Appliquer les calculs automatiques
        if hasattr(self, 'annee_civile_calculee'):
            instance.annee_civile = self.annee_civile_calculee
        if hasattr(self, 'nb_jours_calcule'):
            instance.nb_jours = self.nb_jours_calcule
        
        if commit:
            instance.save()
        
        return instance


class ParametresAnneeForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier les paramètres d'une année.
    """
    class Meta:
        model = ParametresAnnee
        fields = ['annee', 'jours_ouvres_ou_ouvrables']
        widgets = {
            'annee': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'min': ANNEE_MIN,
                'max': ANNEE_MAX,
            }),
            'jours_ouvres_ou_ouvrables': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
            }),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialise le formulaire.

        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés (peut contenir 'user')
        """
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pré-remplir l'année avec l'année courante si nouveaux paramètres
        if not self.instance.pk:
            from datetime import date
            self.fields['annee'].initial = date.today().year

    def clean_annee(self):
        """
        Valide l'année.

        Returns:
            int: Année validée

        Raises:
            ValidationError: Si l'année est invalide
        """
        annee = self.cleaned_data.get('annee')
        
        if annee < ANNEE_MIN or annee > ANNEE_MAX:
            raise ValidationError(
                _('L\'année doit être entre %(min)s et %(max)s.') % {
                    'min': ANNEE_MIN,
                    'max': ANNEE_MAX
                }
            )
        
        # Vérifier qu'il n'existe pas déjà des paramètres pour cet utilisateur et cette année
        if self.user:
            existing = ParametresAnnee.objects.filter(
                user=self.user,
                annee=annee
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(
                    _('Des paramètres existent déjà pour l\'année %(annee)s.') % {'annee': annee}
                )
        
        return annee

    def save(self, commit=True):
        """
        Sauvegarde les paramètres.

        Args:
            commit: Si True, sauvegarde en base de données

        Returns:
            ParametresAnnee: Instance des paramètres sauvegardés
        """
        instance = super().save(commit=False)
        
        if self.user:
            instance.user = self.user
        
        if commit:
            instance.save()
        
        return instance
