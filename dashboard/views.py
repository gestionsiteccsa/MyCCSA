"""
Vues de l'application dashboard.
"""
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from .utils import get_dashboard_stats


def is_superuser(user):
    """
    Vérifie si l'utilisateur est un superutilisateur.

    Args:
        user: Instance de l'utilisateur

    Returns:
        bool: True si superutilisateur, False sinon
    """
    return user.is_authenticated and user.is_superuser


@user_passes_test(is_superuser)
def dashboard_view(request):
    """
    Vue principale du dashboard administrateur.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec le dashboard
    """
    stats = get_dashboard_stats()

    context = {
        'stats': stats,
    }
    return render(request, 'dashboard/index.html', context)

