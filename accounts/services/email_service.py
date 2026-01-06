"""
Service d'envoi d'emails pour l'application accounts.
"""
import logging
from typing import Optional
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailService:
    """
    Service pour gérer l'envoi d'emails aux utilisateurs.
    """

    @staticmethod
    def _should_send_notification(
        user: User, notification_type: str
    ) -> bool:
        """
        Vérifie si une notification doit être envoyée selon les préférences.

        Args:
            user: Utilisateur destinataire
            notification_type: Type de notification ('welcome', 'password_change',
                             'new_login', 'security')

        Returns:
            bool: True si la notification doit être envoyée
        """
        # Les emails obligatoires sont toujours envoyés
        if notification_type in ('verification', 'password_reset'):
            return True

        # Vérifier les préférences pour les autres types
        preference_map = {
            'welcome': 'notify_welcome_email',
            'password_change': 'notify_password_change',
            'new_login': 'notify_new_login',
            'security': 'notify_security_alerts',
        }

        preference_field = preference_map.get(notification_type)
        if preference_field:
            return getattr(user, preference_field, True)

        return True

    @staticmethod
    def send_email(
        subject: str,
        template_name: str,
        context: dict,
        recipient_email: str,
        recipient_user: Optional[User] = None,
        notification_type: Optional[str] = None,
    ) -> bool:
        """
        Envoie un email à un utilisateur.

        Args:
            subject: Sujet de l'email
            template_name: Nom du template HTML de l'email
            context: Contexte pour le template
            recipient_email: Email du destinataire
            recipient_user: Instance User du destinataire (optionnel)
            notification_type: Type de notification pour vérifier les préférences

        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        # Vérifier les préférences si un utilisateur est fourni
        if recipient_user and notification_type:
            if not EmailService._should_send_notification(
                recipient_user, notification_type
            ):
                logger.info(
                    f'Email non envoyé à {recipient_email} '
                    f'(préférence désactivée pour {notification_type})'
                )
                return False

        try:
            # Rendre le template HTML
            html_message = render_to_string(
                f'accounts/emails/{template_name}',
                context
            )

            # Rendre le template texte (fallback)
            template_base = template_name.replace('.html', '')
            text_message = render_to_string(
                f'accounts/emails/{template_base}_text.txt',
                context
            )

            # Envoyer l'email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f'Email envoyé avec succès à {recipient_email}')
            return True

        except Exception as e:
            logger.error(
                f'Erreur lors de l\'envoi de l\'email à {recipient_email}: {e}',
                exc_info=True
            )
            return False

    @staticmethod
    def send_verification_email(user: User, verification_url: str) -> bool:
        """
        Envoie un email de vérification à un utilisateur.

        Args:
            user: Utilisateur à vérifier
            verification_url: URL de vérification avec token

        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        context = {
            'user': user,
            'verification_url': verification_url,
            'site_name': getattr(settings, 'SITE_NAME', 'MyCCSA'),
        }

        return EmailService.send_email(
            subject=_('Vérifiez votre adresse email'),
            template_name='verification.html',
            context=context,
            recipient_email=user.email,
            recipient_user=user,
            notification_type='verification',  # Toujours envoyé
        )

    @staticmethod
    def send_welcome_email(user: User) -> bool:
        """
        Envoie un email de bienvenue à un utilisateur.

        Args:
            user: Nouvel utilisateur

        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        context = {
            'user': user,
            'site_name': getattr(settings, 'SITE_NAME', 'MyCCSA'),
        }

        return EmailService.send_email(
            subject=_('Bienvenue sur {site_name}').format(
                site_name=context['site_name']
            ),
            template_name='welcome.html',
            context=context,
            recipient_email=user.email,
            recipient_user=user,
            notification_type='welcome',
        )

    @staticmethod
    def send_password_reset_email(
        user: User, reset_url: str
    ) -> bool:
        """
        Envoie un email de réinitialisation de mot de passe.

        Args:
            user: Utilisateur qui demande la réinitialisation
            reset_url: URL de réinitialisation avec token

        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        context = {
            'user': user,
            'reset_url': reset_url,
            'site_name': getattr(settings, 'SITE_NAME', 'MyCCSA'),
        }

        return EmailService.send_email(
            subject=_('Réinitialisation de votre mot de passe'),
            template_name='password_reset.html',
            context=context,
            recipient_email=user.email,
            recipient_user=user,
            notification_type='password_reset',  # Toujours envoyé
        )

    @staticmethod
    def send_password_change_email(user: User) -> bool:
        """
        Envoie un email de notification de changement de mot de passe.

        Args:
            user: Utilisateur qui a changé son mot de passe

        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        context = {
            'user': user,
            'site_name': getattr(settings, 'SITE_NAME', 'MyCCSA'),
        }

        return EmailService.send_email(
            subject=_('Votre mot de passe a été modifié'),
            template_name='password_change.html',
            context=context,
            recipient_email=user.email,
            recipient_user=user,
            notification_type='password_change',
        )

    @staticmethod
    def send_new_login_email(user: User, ip_address: str) -> bool:
        """
        Envoie un email de notification de nouvelle connexion.

        Args:
            user: Utilisateur qui s'est connecté
            ip_address: Adresse IP de la connexion

        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        context = {
            'user': user,
            'ip_address': ip_address,
            'site_name': getattr(settings, 'SITE_NAME', 'MyCCSA'),
        }

        return EmailService.send_email(
            subject=_('Nouvelle connexion détectée'),
            template_name='new_login.html',
            context=context,
            recipient_email=user.email,
            recipient_user=user,
            notification_type='new_login',
        )

    @staticmethod
    def send_security_alert_email(
        user: User, alert_message: str, ip_address: Optional[str] = None
    ) -> bool:
        """
        Envoie un email d'alerte de sécurité.

        Args:
            user: Utilisateur concerné
            alert_message: Message d'alerte
            ip_address: Adresse IP (optionnel)

        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        context = {
            'user': user,
            'alert_message': alert_message,
            'ip_address': ip_address,
            'site_name': getattr(settings, 'SITE_NAME', 'MyCCSA'),
        }

        return EmailService.send_email(
            subject=_('Alerte de sécurité'),
            template_name='security_alert.html',
            context=context,
            recipient_email=user.email,
            recipient_user=user,
            notification_type='security',
        )
