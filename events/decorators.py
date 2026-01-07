"""
Décorateurs personnalisés pour l'application events.
"""
import logging
from functools import wraps
from typing import Callable, Any
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from .constants import RATE_LIMIT_UPLOADS_PER_MINUTE

logger = logging.getLogger(__name__)


def rate_limit_uploads(
    max_uploads: int = RATE_LIMIT_UPLOADS_PER_MINUTE,
    window_seconds: int = 60
) -> Callable:
    """
    Décorateur pour limiter le nombre d'uploads par utilisateur.

    Utilise le cache Django pour suivre le nombre d'uploads par utilisateur
    dans une fenêtre de temps donnée.

    Args:
        max_uploads: Nombre maximum d'uploads autorisés dans la fenêtre
        window_seconds: Durée de la fenêtre en secondes (défaut: 60)

    Returns:
        Callable: Fonction décorée

    Example:
        >>> @rate_limit_uploads(max_uploads=10, window_seconds=60)
        >>> def upload_view(request):
        >>>     ...
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: Any, *args: Any, **kwargs: Any) -> HttpResponse:
            # Ne pas limiter les superusers
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Générer une clé de cache unique par utilisateur
            user_id = request.user.id if request.user.is_authenticated else request.META.get('REMOTE_ADDR', 'anonymous')
            cache_key = f'upload_rate_limit_{user_id}'

            # Récupérer le nombre d'uploads actuels
            upload_count = cache.get(cache_key, 0)

            # Vérifier si la limite est dépassée
            if upload_count >= max_uploads:
                logger.warning(
                    f"Rate limit dépassé pour l'utilisateur {user_id}: "
                    f"{upload_count} uploads dans les {window_seconds} dernières secondes"
                )
                return HttpResponse(
                    _('Trop de fichiers uploadés. Veuillez patienter quelques instants avant de réessayer.'),
                    status=429  # 429 Too Many Requests
                )

            # Incrémenter le compteur
            cache.set(cache_key, upload_count + 1, window_seconds)

            # Exécuter la vue
            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator
