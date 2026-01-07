"""
Vues de l'application fractionnement.
"""
import logging
from datetime import date
from typing import Dict, Any
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from .models import CycleHebdomadaire, PeriodeConge, ParametresAnnee, CalculFractionnement
from .forms import CycleHebdomadaireForm, PeriodeCongeForm, ParametresAnneeForm
from .constants import PAGINATION_PAR_PAGE
from .services.calcul_service import (
    calculer_fractionnement_complet,
    get_jours_hors_periode_principale,
    calculer_jours_fractionnement,
)
from .services.calendrier_service import get_calendrier_data

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET", "POST"])
def cycle_create_view(request: HttpRequest) -> HttpResponse:
    """
    Vue pour créer un cycle hebdomadaire.
    """
    if request.method == 'POST':
        form = CycleHebdomadaireForm(request.POST, user=request.user)
        if form.is_valid():
            cycle = form.save()
            # Invalider le cache du calcul pour cette année
            cache.delete(f'calcul_fractionnement_{request.user.id}_{cycle.annee}')
            messages.success(request, _('Cycle hebdomadaire créé avec succès.'))
            return redirect('fractionnement:cycle_list')
    else:
        form = CycleHebdomadaireForm(user=request.user)

    context = {
        'form': form,
        'title': _('Créer un cycle hebdomadaire'),
    }
    return render(request, 'fractionnement/cycle_form.html', context)


@login_required
@require_http_methods(["GET"])
def cycle_list_view(request: HttpRequest) -> HttpResponse:
    """
    Vue pour lister les cycles hebdomadaires de l'utilisateur.
    """
    cycles = CycleHebdomadaire.objects.filter(
        user=request.user
    ).select_related('user').order_by('-annee')

    # Pagination
    paginator = Paginator(cycles, PAGINATION_PAR_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'cycles': page_obj,
    }
    return render(request, 'fractionnement/cycle_list.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def cycle_update_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Vue pour modifier un cycle hebdomadaire.
    """
    cycle = get_object_or_404(
        CycleHebdomadaire,
        pk=pk,
        user=request.user
    )

    if request.method == 'POST':
        form = CycleHebdomadaireForm(request.POST, instance=cycle, user=request.user)
        if form.is_valid():
            cycle = form.save()
            # Invalider le cache du calcul pour cette année
            cache.delete(f'calcul_fractionnement_{request.user.id}_{cycle.annee}')
            messages.success(request, _('Cycle hebdomadaire modifié avec succès.'))
            return redirect('fractionnement:cycle_list')
    else:
        form = CycleHebdomadaireForm(instance=cycle, user=request.user)

    context = {
        'form': form,
        'cycle': cycle,
        'title': _('Modifier le cycle hebdomadaire'),
    }
    return render(request, 'fractionnement/cycle_form.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def cycle_delete_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Vue pour supprimer un cycle hebdomadaire.
    """
    cycle = get_object_or_404(
        CycleHebdomadaire,
        pk=pk,
        user=request.user
    )

    if request.method == 'POST':
        annee = cycle.annee
        cycle.delete()
        # Invalider le cache du calcul pour cette année
        cache.delete(f'calcul_fractionnement_{request.user.id}_{annee}')
        messages.success(request, _('Cycle hebdomadaire supprimé avec succès.'))
        return redirect('fractionnement:cycle_list')

    context = {
        'cycle': cycle,
    }
    return render(request, 'fractionnement/cycle_delete.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def periode_create_view(request: HttpRequest) -> HttpResponse:
    """
    Vue pour créer une période de congé.
    """
    if request.method == 'POST':
        form = PeriodeCongeForm(request.POST, user=request.user)
        if form.is_valid():
            periode = form.save()
            # Invalider les caches pour cette année
            cache.delete(f'calcul_fractionnement_{request.user.id}_{periode.annee_civile}')
            cache.delete(f'calendrier_data_{request.user.id}_{periode.annee_civile}')
            messages.success(request, _('Période de congé créée avec succès.'))
            return redirect('fractionnement:periode_list')
    else:
        form = PeriodeCongeForm(user=request.user)

    context = {
        'form': form,
        'title': _('Créer une période de congé'),
    }
    return render(request, 'fractionnement/periode_form.html', context)


@login_required
@require_http_methods(["GET"])
def periode_list_view(request: HttpRequest) -> HttpResponse:
    """
    Vue pour lister les périodes de congés de l'utilisateur.
    """
    periodes = PeriodeConge.objects.filter(
        user=request.user
    ).select_related('user').order_by('-date_debut')

    # Filtres
    annee = request.GET.get('annee')
    if annee:
        try:
            periodes = periodes.filter(annee_civile=int(annee))
        except ValueError:
            pass

    type_conge = request.GET.get('type_conge')
    if type_conge:
        periodes = periodes.filter(type_conge=type_conge)

    # Pagination
    paginator = Paginator(periodes, PAGINATION_PAR_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'periodes': page_obj,
    }
    return render(request, 'fractionnement/periode_list.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def periode_update_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Vue pour modifier une période de congé.
    """
    periode = get_object_or_404(
        PeriodeConge,
        pk=pk,
        user=request.user
    )

    if request.method == 'POST':
        form = PeriodeCongeForm(request.POST, instance=periode, user=request.user)
        if form.is_valid():
            periode = form.save()
            # Invalider les caches pour cette année
            cache.delete(f'calcul_fractionnement_{request.user.id}_{periode.annee_civile}')
            cache.delete(f'calendrier_data_{request.user.id}_{periode.annee_civile}')
            messages.success(request, _('Période de congé modifiée avec succès.'))
            return redirect('fractionnement:periode_list')
    else:
        form = PeriodeCongeForm(instance=periode, user=request.user)

    context = {
        'form': form,
        'periode': periode,
        'title': _('Modifier la période de congé'),
    }
    return render(request, 'fractionnement/periode_form.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def periode_delete_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Vue pour supprimer une période de congé.
    """
    periode = get_object_or_404(
        PeriodeConge,
        pk=pk,
        user=request.user
    )

    if request.method == 'POST':
        annee = periode.annee_civile
        periode.delete()
        # Invalider les caches pour cette année
        cache.delete(f'calcul_fractionnement_{request.user.id}_{annee}')
        cache.delete(f'calendrier_data_{request.user.id}_{annee}')
        messages.success(request, _('Période de congé supprimée avec succès.'))
        return redirect('fractionnement:periode_list')

    context = {
        'periode': periode,
    }
    return render(request, 'fractionnement/periode_delete.html', context)


@login_required
@require_http_methods(["GET"])
def fractionnement_view(request):
    """
    Vue principale pour le calcul des jours de fractionnement.
    """
    # Récupérer l'année depuis les paramètres GET ou utiliser l'année courante
    annee = request.GET.get('annee')
    if annee:
        try:
            annee = int(annee)
        except ValueError:
            annee = date.today().year
    else:
        annee = date.today().year

    # Récupérer le cycle hebdomadaire pour l'année
    try:
        cycle = CycleHebdomadaire.objects.select_related('user').only(
            'id', 'annee', 'heures_semaine', 'quotite_travail',
            'rtt_annuels', 'conges_annuels', 'jours_ouvres_ou_ouvrables',
            'user__email'
        ).get(
            user=request.user,
            annee=annee
        )
    except CycleHebdomadaire.DoesNotExist:
        cycle = None

    # Récupérer les paramètres de l'année
    try:
        parametres = ParametresAnnee.objects.select_related('user').only(
            'id', 'annee', 'jours_ouvres_ou_ouvrables', 'user__email'
        ).get(
            user=request.user,
            annee=annee
        )
    except ParametresAnnee.DoesNotExist:
        parametres = None

    # Calculer le fractionnement
    try:
        calcul = calculer_fractionnement_complet(request.user, annee)
    except Exception as e:
        logger.error(f"Erreur lors du calcul du fractionnement: {e}")
        calcul = {
            'jours_hors_periode': 0,
            'jours_fractionnement': 0,
            'annee': annee,
        }

    # Récupérer les périodes de congés pour l'année
    periodes = PeriodeConge.objects.filter(
        user=request.user,
        annee_civile=annee
    ).select_related('user').only(
        'id', 'date_debut', 'date_fin', 'type_conge',
        'nb_jours', 'annee_civile', 'user__email'
    ).order_by('date_debut')

    # Compteur au 1er janvier
    date_1er_janvier = date(annee, 1, 1)
    jours_ouvres_ou_ouvrables = 'ouvres'
    if parametres:
        jours_ouvres_ou_ouvrables = parametres.jours_ouvres_ou_ouvrables
    elif cycle:
        jours_ouvres_ou_ouvrables = cycle.jours_ouvres_ou_ouvrables

    from .utils import compter_jours_ouvres, compter_jours_ouvrables
    if jours_ouvres_ou_ouvrables == 'ouvrables':
        compteur_1er_janvier = compter_jours_ouvrables(
            date_1er_janvier,
            date.today(),
            exclure_feries=True,
            annee=annee
        )
    else:
        compteur_1er_janvier = compter_jours_ouvres(
            date_1er_janvier,
            date.today(),
            exclure_feries=True,
            annee=annee
        )

    context = {
        'annee': annee,
        'cycle': cycle,
        'parametres': parametres,
        'calcul': calcul,
        'periodes': periodes,
        'compteur_1er_janvier': compteur_1er_janvier,
        'jours_ouvres_ou_ouvrables': jours_ouvres_ou_ouvrables,
    }
    return render(request, 'fractionnement/index.html', context)


@login_required
@require_http_methods(["GET"])
def api_calendrier_data(request: HttpRequest, annee: str) -> JsonResponse:
    """
    API JSON pour récupérer les données du calendrier.

    Utilise le cache pour optimiser les performances.
    """
    from django.core.cache import cache

    try:
        annee_int = int(annee)
    except ValueError:
        return JsonResponse({'error': 'Année invalide'}, status=400)

    # Cache par utilisateur et année (15 minutes)
    cache_key = f'calendrier_data_{request.user.id}_{annee_int}'
    data = cache.get(cache_key)

    if data is None:
        data = get_calendrier_data(request.user, annee_int)
        cache.set(cache_key, data, 60 * 15)  # 15 minutes

    return JsonResponse(data)


@login_required
@require_http_methods(["GET"])
def api_calcul_fractionnement(request: HttpRequest, annee: str) -> JsonResponse:
    """
    API JSON pour calculer le fractionnement en temps réel.

    Utilise le cache pour optimiser les performances.
    """
    from django.core.cache import cache

    try:
        annee_int = int(annee)
    except ValueError:
        return JsonResponse({'error': 'Année invalide'}, status=400)

    # Cache par utilisateur et année (5 minutes car peut changer avec les périodes)
    cache_key = f'calcul_fractionnement_{request.user.id}_{annee_int}'
    calcul = cache.get(cache_key)

    if calcul is None:
        try:
            calcul = calculer_fractionnement_complet(request.user, annee_int)
            cache.set(cache_key, calcul, 60 * 5)  # 5 minutes
        except ValueError as e:
            logger.warning(f"Erreur de validation lors du calcul du fractionnement pour {request.user.email}, année {annee_int}: {e}")
            return JsonResponse({'error': 'Données invalides pour le calcul'}, status=400)
        except Exception as e:
            logger.error(
                f"Erreur lors du calcul du fractionnement pour {request.user.email}, année {annee_int}: {e}",
                exc_info=True
            )
            return JsonResponse({'error': 'Une erreur est survenue lors du calcul'}, status=500)

    return JsonResponse(calcul)
