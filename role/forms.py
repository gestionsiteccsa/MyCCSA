"""
Formulaires de l'application role.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models import Role

User = get_user_model()


class RoleForm(forms.ModelForm):
    """
    Formulaire pour créer et modifier un rôle.
    """
    class Meta:
        model = Role
        fields = ['nom', 'niveau']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'placeholder': 'Nom du rôle',
                'aria-label': 'Nom du rôle',
                'required': True,
            }),
            'niveau': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'min': '0',
                'aria-label': 'Niveau hiérarchique',
                'required': True,
            }),
        }
        labels = {
            'nom': _('Nom du rôle'),
            'niveau': _('Niveau hiérarchique'),
        }
        help_texts = {
            'niveau': _('Niveau hiérarchique (0 = agents, 1 = coordo, 2 = directeur, etc.)'),
        }

    def clean_nom(self):
        """
        Valide le nom du rôle.

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
                    _('Le nom du rôle doit contenir au moins 2 caractères.')
                )
            if len(nom) > 200:
                raise ValidationError(
                    _('Le nom du rôle ne peut pas dépasser 200 caractères.')
                )
        return nom

    def clean_niveau(self):
        """
        Valide le niveau du rôle.

        Returns:
            int: Niveau validé

        Raises:
            ValidationError: Si le niveau est invalide
        """
        niveau = self.cleaned_data.get('niveau')
        if niveau is not None:
            if niveau < 0:
                raise ValidationError(
                    _('Le niveau doit être un nombre positif ou nul.')
                )
            # Vérifier l'unicité du niveau si on modifie un rôle existant
            if self.instance.pk:
                existing_role = Role.objects.filter(niveau=niveau).exclude(pk=self.instance.pk).first()
                if existing_role:
                    raise ValidationError(
                        _('Un rôle avec le niveau %(niveau)s existe déjà (%(nom)s).') % {
                            'niveau': niveau,
                            'nom': existing_role.nom
                        }
                    )
            else:
                # Nouveau rôle
                existing_role = Role.objects.filter(niveau=niveau).first()
                if existing_role:
                    raise ValidationError(
                        _('Un rôle avec le niveau %(niveau)s existe déjà (%(nom)s).') % {
                            'niveau': niveau,
                            'nom': existing_role.nom
                        }
                    )
        return niveau


class UserRoleForm(forms.Form):
    """
    Formulaire pour attribuer un rôle à un utilisateur.
    """
    role = forms.ModelChoiceField(
        queryset=Role.objects.all().order_by('niveau', 'nom'),
        required=False,
        widget=forms.RadioSelect(attrs={
            'class': 'space-y-2',
        }),
        label=_('Rôle'),
        help_text=_('Sélectionnez le rôle à attribuer à cet utilisateur.')
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
            # Pré-sélectionner le rôle de l'utilisateur
            self.fields['role'].initial = user.role

    def clean_role(self):
        """
        Nettoie et valide le rôle sélectionné.

        Returns:
            Role ou None: Rôle validé

        Raises:
            ValidationError: Si le rôle est invalide
        """
        role = self.cleaned_data.get('role')
        return role
