"""
Vues personnalisées pour la gestion des erreurs.
"""
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse


def handler404(
    request: HttpRequest, exception: Exception
) -> HttpResponse:
    """
    Gestionnaire personnalisé pour les erreurs 404.

    Args:
        request: Objet HttpRequest
        exception: Exception levée

    Returns:
        HttpResponse: Réponse HTTP avec le template 404.html
    """
    return render(request, '404.html', status=404)


def handler500(request: HttpRequest) -> HttpResponse:
    """
    Gestionnaire personnalisé pour les erreurs 500.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec le template 500.html
    """
    return render(request, '500.html', status=500)


def handler403(
    request: HttpRequest, exception: Exception
) -> HttpResponse:
    """
    Gestionnaire personnalisé pour les erreurs 403.

    Args:
        request: Objet HttpRequest
        exception: Exception levée

    Returns:
        HttpResponse: Réponse HTTP avec le template 403.html
    """
    return render(request, '403.html', status=403)


def handler400(
    request: HttpRequest, exception: Exception
) -> HttpResponse:
    """
    Gestionnaire personnalisé pour les erreurs 400.

    Args:
        request: Objet HttpRequest
        exception: Exception levée

    Returns:
        HttpResponse: Réponse HTTP avec le template 400.html
    """
    return render(request, '400.html', status=400)
