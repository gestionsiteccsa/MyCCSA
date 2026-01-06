"""
Fonctions utilitaires de l'application accounts.
"""
import secrets
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


def generate_verification_token() -> str:
    """
    Génère un token sécurisé pour la vérification d'email.

    Returns:
        str: Token de vérification
    """
    return secrets.token_urlsafe(32)


def generate_password_reset_token() -> str:
    """
    Génère un token sécurisé pour la réinitialisation de mot de passe.

    Returns:
        str: Token de réinitialisation
    """
    return secrets.token_urlsafe(32)


def is_verification_token_valid(
    user: User, token: str, expiration_hours: int = 24
) -> bool:
    """
    Vérifie si un token de vérification est valide et n'a pas expiré.

    Args:
        user: Utilisateur concerné
        token: Token à vérifier
        expiration_hours: Nombre d'heures avant expiration (défaut: 24)

    Returns:
        bool: True si le token est valide
    """
    if not user.email_verification_token:
        return False

    if user.email_verification_token != token:
        return False

    if not user.email_verification_sent_at:
        return False

    expiration_time = (
        user.email_verification_sent_at
        + timedelta(hours=expiration_hours)
    )

    return timezone.now() <= expiration_time


def is_password_reset_token_valid(
    user: User, token: str, expiration_hours: int = 1
) -> bool:
    """
    Vérifie si un token de réinitialisation de mot de passe est valide.

    Args:
        user: Utilisateur concerné
        token: Token à vérifier
        expiration_hours: Nombre d'heures avant expiration (défaut: 1)

    Returns:
        bool: True si le token est valide
    """
    if not user.password_reset_token:
        return False

    if user.password_reset_token != token:
        return False

    if not user.password_reset_sent_at:
        return False

    expiration_time = (
        user.password_reset_sent_at
        + timedelta(hours=expiration_hours)
    )

    return timezone.now() <= expiration_time


def is_first_user() -> bool:
    """
    Vérifie si c'est le premier utilisateur du système.

    Returns:
        bool: True si aucun utilisateur n'existe encore
    """
    return not User.objects.exists()


def get_client_ip(request) -> str:
    """
    Récupère l'adresse IP du client depuis la requête.

    Args:
        request: Objet HttpRequest

    Returns:
        str: Adresse IP du client
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip
