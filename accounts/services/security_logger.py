"""
Service de logging pour les événements de sécurité.
"""
import logging
from django.utils import timezone
from django.contrib.auth import get_user_model

logger = logging.getLogger('django.security')
User = get_user_model()

class SecurityLogger:
    """
    Service pour centraliser les logs liés à la sécurité.
    """

    @staticmethod
    def log_login_success(user, ip_address: str):
        """Log une connexion réussie."""
        logger.info(
            f"CONNEXION_REUSSIE | User: {user.email} | IP: {ip_address} | Date: {timezone.now()}"
        )

    @staticmethod
    def log_login_failed(email: str, ip_address: str):
        """Log une tentative de connexion échouée."""
        logger.warning(
            f"CONNEXION_ECHOUEE | Email tenté: {email} | IP: {ip_address} | Date: {timezone.now()}"
        )

    @staticmethod
    def log_password_change(user):
        """Log un changement de mot de passe."""
        logger.info(
            f"CHANGEMENT_MOT_DE_PASSE | User: {user.email} | Date: {timezone.now()}"
        )

    @staticmethod
    def log_password_reset_request(email: str):
        """Log une demande de réinitialisation de mot de passe."""
        logger.info(
            f"DEMANDE_REINITIALISATION | Email: {email} | Date: {timezone.now()}"
        )

    @staticmethod
    def log_account_created(user):
        """Log la création d'un nouveau compte."""
        logger.info(
            f"COMPTE_CREE | User: {user.email} | Superuser: {user.is_superuser} | Date: {timezone.now()}"
        )

    @staticmethod
    def log_security_alert(user, message: str, ip_address: str = None):
        """Log une alerte de sécurité générale."""
        logger.error(
            f"ALERTE_SECURITE | User: {user.email if user else 'N/A'} | Message: {message} | IP: {ip_address} | Date: {timezone.now()}"
        )
