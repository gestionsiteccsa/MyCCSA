"""
Vues de l'application role.
"""
import logging
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db import transaction, models
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from .models import Role
from .forms import RoleForm, UserRoleForm

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
def role_list_view(request):
    """
    Vue pour lister tous les rôles.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec la liste des rôles
    """
    # Optimisation : charger les rôles avec le nombre d'utilisateurs
    roles = Role.objects.annotate(
        user_count=Count('utilisateurs')
    ).only('nom', 'niveau', 'created_at').order_by('niveau', 'nom')

    # Pagination
    paginator = Paginator(roles, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'roles': page_obj,
    }
    return render(request, 'role/list.html', context)


@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def role_create_view(request):
    """
    Vue pour créer un nouveau rôle.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec le formulaire ou redirection
    """
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            role = form.save()
            logger.info(f'Rôle créé: {role.nom} (niveau {role.niveau}) par {request.user.email}')
            messages.success(
                request,
                _('Le rôle "%(nom)s" a été créé avec succès.') % {'nom': role.nom}
            )
            return redirect('role:list')
    else:
        form = RoleForm()

    context = {
        'form': form,
        'title': _('Créer un rôle'),
    }
    return render(request, 'role/create.html', context)


@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def role_update_view(request, pk):
    """
    Vue pour modifier un rôle existant.

    Args:
        request: Objet HttpRequest
        pk: Clé primaire du rôle

    Returns:
        HttpResponse: Réponse HTTP avec le formulaire ou redirection
    """
    role = get_object_or_404(Role, pk=pk)

    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role)
        if form.is_valid():
            role = form.save()
            logger.info(f'Rôle modifié: {role.nom} (niveau {role.niveau}) par {request.user.email}')
            messages.success(
                request,
                _('Le rôle "%(nom)s" a été modifié avec succès.') % {'nom': role.nom}
            )
            return redirect('role:list')
    else:
        form = RoleForm(instance=role)

    context = {
        'form': form,
        'role': role,
        'title': _('Modifier le rôle'),
    }
    return render(request, 'role/update.html', context)


@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def role_delete_view(request, pk):
    """
    Vue pour supprimer un rôle.

    Args:
        request: Objet HttpRequest
        pk: Clé primaire du rôle

    Returns:
        HttpResponse: Réponse HTTP avec confirmation ou redirection
    """
    role = get_object_or_404(
        Role.objects.annotate(user_count=Count('utilisateurs')),
        pk=pk
    )
    user_count = role.user_count

    if request.method == 'POST':
        nom = role.nom
        role.delete()
        logger.info(f'Rôle supprimé: {nom} par {request.user.email}')
        messages.success(
            request,
            _('Le rôle "%(nom)s" a été supprimé avec succès.') % {'nom': nom}
        )
        return redirect('role:list')

    context = {
        'role': role,
        'user_count': user_count,
    }
    return render(request, 'role/delete.html', context)


@user_passes_test(is_superuser)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def user_role_view(request, user_id):
    """
    Vue pour attribuer un rôle à un utilisateur.

    Args:
        request: Objet HttpRequest
        user_id: ID de l'utilisateur

    Returns:
        HttpResponse: Réponse HTTP avec le formulaire ou redirection
    """
    user = get_object_or_404(
        User.objects.select_related('role'),
        pk=user_id
    )

    if request.method == 'POST':
        form = UserRoleForm(request.POST, user=user)
        if form.is_valid():
            # Mettre à jour le rôle de l'utilisateur
            user.role = form.cleaned_data['role']
            user.save()
            logger.info(
                f'Rôle mis à jour pour {user.email} par {request.user.email}'
            )
            messages.success(
                request,
                _('Le rôle de %(user)s a été mis à jour avec succès.') % {
                    'user': user.get_full_name() or user.email
                }
            )
            return redirect('role:user_role', user_id=user.id)
    else:
        form = UserRoleForm(user=user)

    # Récupérer tous les rôles pour l'affichage
    all_roles = Role.objects.only('id', 'nom', 'niveau').order_by('niveau', 'nom')

    context = {
        'form': form,
        'user': user,
        'all_roles': all_roles,
    }
    return render(request, 'role/user_role.html', context)


@user_passes_test(is_superuser)
@require_http_methods(["GET"])
def check_level_available(request):
    """
    Vue API pour vérifier si un niveau est disponible.

    Args:
        request: Objet HttpRequest avec paramètre 'niveau' et optionnel 'exclude_pk'

    Returns:
        JsonResponse: {'available': bool, 'existing_role': str ou None}
    """
    niveau = request.GET.get('niveau')
    exclude_pk = request.GET.get('exclude_pk')

    if not niveau:
        return JsonResponse({'error': 'Niveau manquant'}, status=400)

    try:
        niveau = int(niveau)
    except ValueError:
        return JsonResponse({'error': 'Niveau invalide'}, status=400)

    qs = Role.objects.filter(niveau=niveau)
    if exclude_pk:
        try:
            qs = qs.exclude(pk=int(exclude_pk))
        except ValueError:
            pass

    existing_role = qs.first()

    return JsonResponse({
        'available': existing_role is None,
        'existing_role': existing_role.nom if existing_role else None
    })


@user_passes_test(is_superuser)
@require_http_methods(["GET"])
def user_list_view(request):
    """
    Vue pour lister tous les utilisateurs avec leurs rôles.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec la liste des utilisateurs
    """
    users = User.objects.select_related('role').all().order_by('-date_joined')

    # Pagination
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'users': page_obj,
    }
    return render(request, 'role/user_list.html', context)
