"""
Modèles de l'application accounts.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Gestionnaire personnalisé pour le modèle User.
    """
    def create_user(
        self, email: str, password: str = None, **extra_fields
    ):
        """
        Crée et sauvegarde un utilisateur avec l'email et le mot de passe.

        Args:
            email: Email de l'utilisateur (identifiant unique)
            password: Mot de passe de l'utilisateur
            **extra_fields: Champs supplémentaires (first_name, last_name, etc.)

        Returns:
            User: Instance de l'utilisateur créé
        """
        if not email:
            raise ValueError(_('Les utilisateurs doivent avoir une adresse email'))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self, email: str, password: str = None, **extra_fields
    ):
        """
        Crée et sauvegarde un superutilisateur.

        Args:
            email: Email du superutilisateur
            password: Mot de passe du superutilisateur
            **extra_fields: Champs supplémentaires

        Returns:
            User: Instance du superutilisateur créé
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('email_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(
                _('Le superutilisateur doit avoir is_staff=True.')
            )
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(
                _('Le superutilisateur doit avoir is_superuser=True.')
            )

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modèle User personnalisé utilisant l'email comme identifiant unique.
    """
    email = models.EmailField(
        _('adresse email'),
        unique=True,
        db_index=True,
        help_text=_('Adresse email utilisée comme identifiant unique')
    )
    first_name = models.CharField(
        _('prénom'),
        max_length=150,
        blank=True,
        db_index=True
    )
    last_name = models.CharField(
        _('nom'),
        max_length=150,
        blank=True,
        db_index=True
    )

    # Champs Django standards
    is_active = models.BooleanField(
        _('actif'),
        default=True,
        db_index=True,
        help_text=_(
            'Désigne si cet utilisateur doit être traité comme actif. '
            'Désélectionnez ceci au lieu de supprimer le compte.'
        )
    )
    is_staff = models.BooleanField(
        _('membre du staff'),
        default=False,
        db_index=True,
        help_text=_(
            'Désigne si l\'utilisateur peut se connecter à ce site admin.'
        )
    )
    date_joined = models.DateTimeField(
        _('date d\'inscription'),
        default=timezone.now,
        db_index=True
    )

    # Vérification email
    email_verified = models.BooleanField(
        _('email vérifié'),
        default=False,
        db_index=True,
        help_text=_('Désigne si l\'email de l\'utilisateur a été vérifié.')
    )
    email_verification_token = models.CharField(
        _('token de vérification email'),
        max_length=100,
        blank=True,
        null=True,
        db_index=True
    )
    email_verification_sent_at = models.DateTimeField(
        _('date d\'envoi du token de vérification'),
        null=True,
        blank=True
    )

    # Réinitialisation de mot de passe
    password_reset_token = models.CharField(
        _('token de réinitialisation de mot de passe'),
        max_length=100,
        blank=True,
        null=True,
        db_index=True
    )
    password_reset_sent_at = models.DateTimeField(
        _('date d\'envoi du token de réinitialisation'),
        null=True,
        blank=True
    )

    # Préférences de notifications
    notify_welcome_email = models.BooleanField(
        _('notifier email de bienvenue'),
        default=True,
        help_text=_('Recevoir un email de bienvenue lors de l\'inscription')
    )
    notify_password_change = models.BooleanField(
        _('notifier changement de mot de passe'),
        default=True,
        help_text=_('Recevoir un email lors du changement de mot de passe')
    )
    notify_new_login = models.BooleanField(
        _('notifier nouvelle connexion'),
        default=True,
        help_text=_('Recevoir un email lors d\'une nouvelle connexion')
    )
    notify_security_alerts = models.BooleanField(
        _('notifier alertes de sécurité'),
        default=True,
        help_text=_(
            'Recevoir des emails pour les alertes de sécurité '
            '(nouvelle connexion depuis un nouvel appareil, etc.)'
        )
    )

    # Secteurs
    secteurs = models.ManyToManyField(
        'secteurs.Secteur',
        related_name='utilisateurs',
        blank=True,
        verbose_name=_('secteurs'),
        help_text=_('Secteurs d\'activité associés à cet utilisateur')
    )

    # Rôle
    role = models.ForeignKey(
        'role.Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='utilisateurs',
        verbose_name=_('rôle'),
        help_text=_('Rôle hiérarchique de l\'utilisateur')
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active', 'email_verified']),
            models.Index(fields=['-date_joined']),
        ]

    def __str__(self) -> str:
        """
        Retourne la représentation string de l'utilisateur.

        Returns:
            str: Email de l'utilisateur
        """
        return self.email

    def get_full_name(self) -> str:
        """
        Retourne le nom complet de l'utilisateur.

        Returns:
            str: Prénom et nom ou email si non renseigné
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.email

    def get_short_name(self) -> str:
        """
        Retourne le prénom ou l'email de l'utilisateur.

        Returns:
            str: Prénom ou email
        """
        return self.first_name if self.first_name else self.email
