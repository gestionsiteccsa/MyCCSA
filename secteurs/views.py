"""
Vues de l'application secteurs.
"""
import logging
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from .models import Secteur
from .forms import SecteurForm, UserSecteursForm

logger = logging.getLogger(__name__)
User = get_user_model()


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
@require_http_methods(["GET"])
def secteur_list_view(request):
    """
    Vue pour lister tous les secteurs.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec la liste des secteurs
    """
    # Optimisation : ne charger que les champs nécessaires pour éviter de charger
    # les relations ManyToMany et autres champs inutiles
    secteurs = Secteur.objects.only('nom', 'couleur', 'ordre').order_by('ordre', 'nom')

    # Pagination
    paginator = Paginator(secteurs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'secteurs': page_obj,
    }
    return render(request, 'secteurs/list.html', context)


@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def secteur_create_view(request):
    """
    Vue pour créer un nouveau secteur.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec le formulaire ou redirection
    """
    if request.method == 'POST':
        form = SecteurForm(request.POST)
        if form.is_valid():
            secteur = form.save()
            logger.info(f'Secteur créé: {secteur.nom} par {request.user.email}')
            messages.success(
                request,
                _('Le secteur "%(nom)s" a été créé avec succès.') % {'nom': secteur.nom}
            )
            return redirect('secteurs:list')
    else:
        form = SecteurForm()

    context = {
        'form': form,
        'title': _('Créer un secteur'),
    }
    return render(request, 'secteurs/create.html', context)


@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def secteur_update_view(request, pk):
    """
    Vue pour modifier un secteur existant.

    Args:
        request: Objet HttpRequest
        pk: Clé primaire du secteur

    Returns:
        HttpResponse: Réponse HTTP avec le formulaire ou redirection
    """
    secteur = get_object_or_404(Secteur, pk=pk)

    if request.method == 'POST':
        form = SecteurForm(request.POST, instance=secteur)
        if form.is_valid():
            secteur = form.save()
            logger.info(f'Secteur modifié: {secteur.nom} par {request.user.email}')
            messages.success(
                request,
                _('Le secteur "%(nom)s" a été modifié avec succès.') % {'nom': secteur.nom}
            )
            return redirect('secteurs:list')
    else:
        form = SecteurForm(instance=secteur)

    context = {
        'form': form,
        'secteur': secteur,
        'title': _('Modifier le secteur'),
    }
    return render(request, 'secteurs/update.html', context)


@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def secteur_delete_view(request, pk):
    """
    Vue pour supprimer un secteur.

    Args:
        request: Objet HttpRequest
        pk: Clé primaire du secteur

    Returns:
        HttpResponse: Réponse HTTP avec confirmation ou redirection
    """
    from django.db.models import Count

    secteur = get_object_or_404(
        Secteur.objects.annotate(user_count=Count('utilisateurs')),
        pk=pk
    )
    user_count = secteur.user_count

    if request.method == 'POST':
        nom = secteur.nom
        secteur.delete()
        logger.info(f'Secteur supprimé: {nom} par {request.user.email}')
        messages.success(
            request,
            _('Le secteur "%(nom)s" a été supprimé avec succès.') % {'nom': nom}
        )
        return redirect('secteurs:list')

    context = {
        'secteur': secteur,
        'user_count': user_count,
    }
    return render(request, 'secteurs/delete.html', context)


@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def user_secteurs_view(request, user_id):
    """
    Vue pour attribuer des secteurs à un utilisateur.

    Args:
        request: Objet HttpRequest
        user_id: ID de l'utilisateur

    Returns:
        HttpResponse: Réponse HTTP avec le formulaire ou redirection
    """
    user = get_object_or_404(
        User.objects.prefetch_related('secteurs'),
        pk=user_id
    )

    if request.method == 'POST':
        # Filtrer les valeurs vides dans request.POST avant de créer le formulaire
        post_data = request.POST.copy()
        if 'secteurs' in post_data:
            secteurs_list = post_data.getlist('secteurs')
            # Filtrer les valeurs vides
            secteurs_filtered = [s for s in secteurs_list if s and s.strip()]
            post_data.setlist('secteurs', secteurs_filtered)

        form = UserSecteursForm(post_data, user=user)
        if form.is_valid():
            # Mettre à jour les secteurs de l'utilisateur
            user.secteurs.set(form.cleaned_data['secteurs'])
            logger.info(
                f'Secteurs mis à jour pour {user.email} par {request.user.email}'
            )
            messages.success(
                request,
                _('Les secteurs de %(user)s ont été mis à jour avec succès.') % {
                    'user': user.get_full_name() or user.email
                }
            )
            return redirect('secteurs:user_secteurs', user_id=user.id)
    else:
        form = UserSecteursForm(user=user)

    # Récupérer tous les secteurs pour l'affichage
    all_secteurs = Secteur.objects.only('id', 'nom', 'couleur', 'ordre').order_by('ordre', 'nom')

    context = {
        'form': form,
        'user': user,
        'all_secteurs': all_secteurs,
    }
    return render(request, 'secteurs/user_secteurs.html', context)


@user_passes_test(is_superuser)
@require_http_methods(["GET"])
def user_list_view(request):
    """
    Vue pour lister tous les utilisateurs avec leurs secteurs.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec la liste des utilisateurs
    """
    users = User.objects.prefetch_related('secteurs').all().order_by('-date_joined')

    # Pagination
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'users': page_obj,
    }
    return render(request, 'secteurs/user_list.html', context)
