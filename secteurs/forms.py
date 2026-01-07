"""
Formulaires de l'application secteurs.
"""
import re
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models import Secteur

User = get_user_model()


class SecteurForm(forms.ModelForm):
    """
    Formulaire pour créer et modifier un secteur.
    """
    class Meta:
        model = Secteur
        fields = ['nom', 'couleur', 'ordre']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'placeholder': 'Nom du secteur',
                'aria-label': 'Nom du secteur',
                'required': True,
            }),
            'couleur': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-custom-blue focus:border-transparent font-mono',
                'placeholder': '#1f4d9b',
                'pattern': '^#[0-9A-Fa-f]{6}$',
                'aria-label': 'Couleur du secteur (format hexadécimal)',
                'required': True,
            }),
            'ordre': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'min': '0',
                'aria-label': 'Ordre d\'affichage',
                'required': True,
            }),
        }
        labels = {
            'nom': _('Nom du secteur'),
            'couleur': _('Couleur'),
            'ordre': _('Ordre d\'affichage'),
        }
        help_texts = {
            'couleur': _('Code couleur hexadécimal (ex: #1f4d9b)'),
            'ordre': _('Ordre d\'affichage (0 = premier)'),
        }

    def clean_couleur(self):
        """
        Valide le format de la couleur hexadécimale.

        Returns:
            str: Code couleur validé

        Raises:
            ValidationError: Si le format est invalide
        """
        couleur = self.cleaned_data.get('couleur')
        if couleur:
            # Supprimer le # si présent
            couleur = couleur.lstrip('#')
            # Vérifier que c'est un code hexadécimal valide (6 caractères)
            if not re.match(r'^[0-9A-Fa-f]{6}$', couleur):
                raise ValidationError(
                    _('Le code couleur doit être au format hexadécimal (ex: 1f4d9b ou #1f4d9b)')
                )
            # Retourner avec le #
            return f'#{couleur.upper()}'
        return couleur

    def clean_nom(self):
        """
        Valide le nom du secteur.

        Returns:
            str: Nom validé

        Raises:
            ValidationError: Si le nom est vide ou trop long
        """
        nom = self.cleaned_data.get('nom')
        if nom:
            nom = nom.strip()
            if len(nom) < 2:
                raise ValidationError(
                    _('Le nom du secteur doit contenir au moins 2 caractères.')
                )
            if len(nom) > 200:
                raise ValidationError(
                    _('Le nom du secteur ne peut pas dépasser 200 caractères.')
                )
        return nom


class UserSecteursForm(forms.Form):
    """
    Formulaire pour attribuer des secteurs à un utilisateur.
    """
    secteurs = forms.ModelMultipleChoiceField(
        queryset=Secteur.objects.all().order_by('ordre', 'nom'),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'space-y-2',
        }),
        label=_('Secteurs'),
        help_text=_('Sélectionnez les secteurs à attribuer à cet utilisateur.')
    )

    def __init__(self, *args, **kwargs):
        """
        Initialise le formulaire avec l'utilisateur.

        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés (peut contenir 'user')
        """
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            # Pré-sélectionner les secteurs de l'utilisateur
            self.fields['secteurs'].initial = user.secteurs.all()

    def clean_secteurs(self):
        """
        Nettoie et valide les secteurs sélectionnés.

        Returns:
            QuerySet: Secteurs validés

        Raises:
            ValidationError: Si les secteurs sont invalides
        """
        secteurs = self.cleaned_data.get('secteurs', [])
        # Filtrer les valeurs vides (déjà fait par ModelMultipleChoiceField, mais on s'assure)
        return secteurs
