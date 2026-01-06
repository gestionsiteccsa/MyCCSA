"""
Vues de l'application home.
"""
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse


def home(request: HttpRequest) -> HttpResponse:
    """
    Vue de la page d'accueil.

    Args:
        request: Objet HttpRequest contenant les métadonnées de la requête

    Returns:
        HttpResponse: Réponse HTTP avec le template de la page d'accueil
    """
    return render(request, "home/index.html")
