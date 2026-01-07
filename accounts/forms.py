"""
Formulaires de l'application accounts.
"""
from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserRegistrationForm(forms.ModelForm):
    """
    Formulaire d'inscription utilisateur.
    """
    password1 = forms.CharField(
        label=_('Mot de passe'),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'autocomplete': 'new-password',
            'aria-describedby': 'password1-help'
        }),
        help_text=_(
            'Votre mot de passe doit contenir au moins 8 caractères '
            'et ne doit pas être trop similaire à vos autres informations.'
        )
    )
    password2 = forms.CharField(
        label=_('Confirmation du mot de passe'),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'autocomplete': 'new-password',
            'aria-describedby': 'password2-help'
        }),
        help_text=_('Entrez le même mot de passe pour vérification.')
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'autocomplete': 'email',
                'aria-required': 'true',
                'aria-describedby': 'email-help'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'autocomplete': 'given-name',
                'aria-describedby': 'first_name-help'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'autocomplete': 'family-name',
                'aria-describedby': 'last_name-help'
            }),
        }
        labels = {
            'email': _('Adresse email'),
            'first_name': _('Prénom'),
            'last_name': _('Nom'),
        }
        help_texts = {
            'email': _('Votre adresse email sera utilisée pour vous connecter.'),
            'first_name': _('Votre prénom (optionnel).'),
            'last_name': _('Votre nom (optionnel).'),
        }

    def clean_email(self):
        """
        Valide que l'email n'est pas déjà utilisé.

        Returns:
            str: Email validé

        Raises:
            ValidationError: Si l'email est déjà utilisé
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                _('Un compte avec cette adresse email existe déjà.')
            )
        return email

    def clean_password1(self):
        """
        Valide le mot de passe avec les validateurs Django.

        Returns:
            str: Mot de passe validé

        Raises:
            ValidationError: Si le mot de passe ne respecte pas les règles
        """
        password1 = self.cleaned_data.get('password1')
        if password1:
            # Valider le mot de passe avec les validateurs Django
            try:
                password_validation.validate_password(password1, self.instance if hasattr(self, 'instance') else None)
            except ValidationError as e:
                raise ValidationError(e.messages)
        return password1

    def clean_password2(self):
        """
        Valide que les deux mots de passe correspondent.

        Returns:
            str: Mot de passe confirmé

        Raises:
            ValidationError: Si les mots de passe ne correspondent pas
        """
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError(_('Les mots de passe ne correspondent pas.'))
        return password2

    def save(self, commit=True):
        """
        Sauvegarde l'utilisateur avec le mot de passe hashé.

        Args:
            commit: Si True, sauvegarde l'utilisateur en base

        Returns:
            User: Instance de l'utilisateur créé
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    """
    Formulaire de connexion utilisateur.
    """
    email = forms.EmailField(
        label=_('Adresse email'),
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'autocomplete': 'email',
            'aria-required': 'true',
            'aria-describedby': 'email-help'
        }),
        help_text=_('Entrez votre adresse email.')
    )
    password = forms.CharField(
        label=_('Mot de passe'),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'autocomplete': 'current-password',
            'aria-required': 'true',
            'aria-describedby': 'password-help'
        }),
        help_text=_('Entrez votre mot de passe.')
    )
    remember_me = forms.BooleanField(
        label=_('Se souvenir de moi'),
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
            'aria-describedby': 'remember_me-help'
        }),
        help_text=_('Rester connecté sur cet appareil.')
    )


class UserProfileEditForm(forms.ModelForm):
    """
    Formulaire d'édition du profil utilisateur.
    """
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'autocomplete': 'email',
                'aria-required': 'true',
                'aria-describedby': 'email-help'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'autocomplete': 'given-name',
                'aria-describedby': 'first_name-help'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'autocomplete': 'family-name',
                'aria-describedby': 'last_name-help'
            }),
        }
        labels = {
            'email': _('Adresse email'),
            'first_name': _('Prénom'),
            'last_name': _('Nom'),
        }
        help_texts = {
            'email': _('Votre adresse email sera utilisée pour vous connecter.'),
            'first_name': _('Votre prénom (optionnel).'),
            'last_name': _('Votre nom (optionnel).'),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialise le formulaire avec l'instance utilisateur.
        """
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        """
        Valide que l'email n'est pas déjà utilisé par un autre utilisateur.

        Returns:
            str: Email validé

        Raises:
            ValidationError: Si l'email est déjà utilisé par un autre utilisateur
        """
        email = self.cleaned_data.get('email')
        if (self.user
                and User.objects.filter(email=email).exclude(pk=self.user.pk).exists()):
            raise ValidationError(
                _('Un compte avec cette adresse email existe déjà.')
            )
        return email


class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Formulaire personnalisé de changement de mot de passe.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise le formulaire avec les classes Tailwind.
        """
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'autocomplete': 'current-password',
            'aria-required': 'true',
            'aria-describedby': 'old_password-help'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'autocomplete': 'new-password',
            'aria-required': 'true',
            'aria-describedby': 'new_password1-help'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'autocomplete': 'new-password',
            'aria-required': 'true',
            'aria-describedby': 'new_password2-help'
        })


class PasswordResetRequestForm(forms.Form):
    """
    Formulaire de demande de réinitialisation de mot de passe.
    """
    email = forms.EmailField(
        label=_('Adresse email'),
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'autocomplete': 'email',
            'aria-required': 'true',
            'aria-describedby': 'email-help'
        }),
        help_text=_(
            'Entrez votre adresse email et nous vous enverrons '
            'un lien pour réinitialiser votre mot de passe.'
        )
    )


class PasswordResetConfirmForm(forms.Form):
    """
    Formulaire de confirmation de réinitialisation de mot de passe.
    """
    new_password1 = forms.CharField(
        label=_('Nouveau mot de passe'),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'autocomplete': 'new-password',
            'aria-required': 'true',
            'aria-describedby': 'new_password1-help'
        }),
        help_text=_(
            'Votre mot de passe doit contenir au moins 8 caractères '
            'et ne doit pas être trop similaire à vos autres informations.'
        )
    )
    new_password2 = forms.CharField(
        label=_('Confirmation du nouveau mot de passe'),
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'autocomplete': 'new-password',
            'aria-required': 'true',
            'aria-describedby': 'new_password2-help'
        }),
        help_text=_('Entrez le même mot de passe pour vérification.')
    )

    def clean_new_password2(self):
        """
        Valide que les deux mots de passe correspondent.

        Returns:
            str: Mot de passe confirmé

        Raises:
            ValidationError: Si les mots de passe ne correspondent pas
        """
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError(_('Les mots de passe ne correspondent pas.'))
        return password2


class NotificationSettingsForm(forms.ModelForm):
    """
    Formulaire de gestion des préférences de notifications.
    """
    class Meta:
        model = User
        fields = (
            'notify_welcome_email',
            'notify_password_change',
            'notify_new_login',
            'notify_security_alerts',
        )
        widgets = {
            'notify_welcome_email': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
                'aria-describedby': 'notify_welcome_email-help'
            }),
            'notify_password_change': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
                'aria-describedby': 'notify_password_change-help'
            }),
            'notify_new_login': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
                'aria-describedby': 'notify_new_login-help'
            }),
            'notify_security_alerts': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500',
                'aria-describedby': 'notify_security_alerts-help'
            }),
        }
        labels = {
            'notify_welcome_email': _('Email de bienvenue'),
            'notify_password_change': _('Changement de mot de passe'),
            'notify_new_login': _('Nouvelle connexion'),
            'notify_security_alerts': _('Alertes de sécurité'),
        }
        help_texts = {
            'notify_welcome_email': _(
                'Recevoir un email de bienvenue lors de l\'inscription'
            ),
            'notify_password_change': _(
                'Recevoir un email lors du changement de mot de passe'
            ),
            'notify_new_login': _(
                'Recevoir un email lors d\'une nouvelle connexion'
            ),
            'notify_security_alerts': _(
                'Recevoir des emails pour les alertes de sécurité '
                '(nouvelle connexion depuis un nouvel appareil, etc.)'
            ),
        }
