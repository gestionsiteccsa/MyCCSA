"""
Vues de l'application events.
"""
import logging
import locale
import os
from collections import defaultdict
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from .models import Event, EventFile, EventAddress
from .forms import EventForm, EventFileForm
from .utils import compress_and_optimize_image, process_event_images, get_secteurs_for_display
from .constants import TIMELINE_EVENTS_LIMIT, MAX_FILE_SIZE, CACHE_DURATION_STATS
from .decorators import rate_limit_uploads

logger = logging.getLogger(__name__)
User = get_user_model()


def can_manage_events(user) -> bool:
    """
    Vérifie si l'utilisateur peut gérer les événements.
    
    Basé sur les groupes Django. L'utilisateur doit être dans un groupe
    ayant la permission events.add_event ou être superuser.

    Args:
        user: Instance de l'utilisateur

    Returns:
        bool: True si l'utilisateur peut gérer les événements
    """
    if not user.is_authenticated:
        return False
    
    # Les superusers peuvent toujours gérer les événements
    if user.is_superuser:
        return True
    
    # Vérifier les permissions via les groupes
    return user.has_perm('events.add_event') or user.has_perm('events.change_event')


def is_dga(user) -> bool:
    """
    Vérifie si l'utilisateur a le rôle DGA.

    Args:
        user: Instance de l'utilisateur

    Returns:
        bool: True si l'utilisateur a le rôle DGA, False sinon
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.role and user.role.nom == 'DGA'


def can_view_event_stats(user):
    """
    Vérifie si l'utilisateur peut voir les statistiques des événements.
    
    Accessible aux superusers et au rôle 'Chargé de communication'.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.role and user.role.nom == 'Chargé de communication'


@user_passes_test(can_view_event_stats)
@require_http_methods(["GET"])
def event_stats_view(request: HttpRequest) -> HttpResponse:
    """
    Vue optimisée pour afficher les statistiques des événements.
    
    Utilise des annotations pour calculer toutes les statistiques en une seule requête
    au lieu de plusieurs count() séparés.
    Utilise le cache pour améliorer les performances (10 minutes).
    
    Accessible au Chargé de communication et Superadmin.
    
    Args:
        request: Objet HttpRequest
        
    Returns:
        HttpResponse: Réponse HTTP avec les statistiques
        
    Example:
        La vue calcule :
        - Total d'événements
        - Répartition par mois (année courante)
        - Répartition par secteur
        - Statuts de validation (en_attente, valides, refuses)
    """
    from django.db.models import Count, Q, Case, When, IntegerField
    from django.db.models.functions import TruncMonth

    # Vérifier le cache (cacher le contexte, pas la réponse HTTP)
    cache_key = 'event_stats_view'
    cached_context = cache.get(cache_key)
    if cached_context is not None:
        return render(request, 'events/stats.html', cached_context)

    now = timezone.now()
    current_year = now.year

    # Optimisation : Calculer toutes les statistiques en une seule requête avec annotations
    # Cela évite les multiples count() séparés qui génèrent plusieurs requêtes SQL
    stats_queryset = Event.objects.annotate(
        # Annoter chaque événement avec son statut de validation
        is_en_attente=Case(
            When(
                Q(statut_validation_dga='en_attente') | Q(statut_validation_dgs='en_attente'),
                then=1
            ),
            default=0,
            output_field=IntegerField()
        ),
        is_valide=Case(
            When(
                statut_validation_dga='valide',
                statut_validation_dgs='valide',
                then=1
            ),
            default=0,
            output_field=IntegerField()
        ),
        is_refuse=Case(
            When(
                Q(statut_validation_dga='refuse') | Q(statut_validation_dgs='refuse'),
                then=1
            ),
            default=0,
            output_field=IntegerField()
        ),
    ).aggregate(
        total_events=Count('id'),
        en_attente=Count('id', filter=Q(statut_validation_dga='en_attente') | Q(statut_validation_dgs='en_attente')),
        valides=Count('id', filter=Q(statut_validation_dga='valide') & Q(statut_validation_dgs='valide')),
        refuses=Count('id', filter=Q(statut_validation_dga='refuse') | Q(statut_validation_dgs='refuse')),
    )

    # 2. Répartition par mois (année courante) - déjà optimisée avec annotate
    events_per_month = Event.objects.filter(
        date_debut__year=current_year
    ).annotate(
        month=TruncMonth('date_debut')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')

    # Formater pour le template
    months_data = []
    for item in events_per_month:
        months_data.append({
            'month': item['month'],
            'count': item['count']
        })

    # 3. Répartition par secteur - déjà optimisée avec annotate
    events_by_sector = Event.objects.values(
        'secteurs__nom', 'secteurs__couleur'
    ).annotate(
        count=Count('id')
    ).order_by('-count')

    # 4. Statuts de validation (depuis l'agrégation optimisée)
    validation_stats = {
        'en_attente': stats_queryset['en_attente'],
        'valides': stats_queryset['valides'],
        'refuses': stats_queryset['refuses'],
    }

    context = {
        'total_events': stats_queryset['total_events'],
        'months_data': months_data,
        'events_by_sector': events_by_sector,
        'validation_stats': validation_stats,
        'current_year': current_year,
    }
    
    # Mettre en cache le contexte pour 10 minutes (pas la réponse HTTP)
    # Le contexte est sérialisable, contrairement à HttpResponse
    cache.set(cache_key, context, CACHE_DURATION_STATS)
    
    return render(request, 'events/stats.html', context)



def is_dgs(user) -> bool:
    """
    Vérifie si l'utilisateur a le rôle DGS.

    Args:
        user: Instance de l'utilisateur

    Returns:
        bool: True si l'utilisateur est DGS
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    if hasattr(user, 'role') and user.role:
        return user.role.nom.upper() == 'DGS'
    return False


def can_validate_events(user) -> bool:
    """
    Vérifie si l'utilisateur peut valider des événements (DGA ou DGS).

    Args:
        user: Instance de l'utilisateur

    Returns:
        bool: True si l'utilisateur peut valider
    """
    return is_dga(user) or is_dgs(user)


@user_passes_test(can_manage_events)
@require_http_methods(["GET"])
def event_calendar_view(request: HttpRequest) -> HttpResponse:
    """
    Vue pour afficher le calendrier des événements.
    
    Utilise le cache pour optimiser les performances.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec le calendrier
    """
    # Cache par secteur (5 minutes)
    secteur_id = request.GET.get('secteur', 'all')
    cache_key = f'event_calendar_{secteur_id}'
    events = cache.get(cache_key)
    
    if events is None:
        # Récupérer tous les événements pour le calendrier
        # Optimisation : charger uniquement les champs nécessaires pour le calendrier
        events = Event.objects.select_related(
            'createur', 'adresse'
        ).prefetch_related(
            'secteurs', 'fichiers'
        ).only(
            'id', 'titre', 'lieu', 'date_debut', 'date_fin',
            'couleur_calendrier', 'adresse__ville', 'adresse__code_postal',
            'createur__first_name', 'createur__last_name'
        ).order_by('date_debut')
        
        # Filtrer par secteur si demandé
        if secteur_id != 'all':
            try:
                events = events.filter(secteurs__id=int(secteur_id))
            except ValueError:
                pass
        
        # Convertir en liste pour le cache (QuerySet n'est pas sérialisable)
        events = list(events)
        cache.set(cache_key, events, 60 * 5)  # 5 minutes
    
    context = {
        'events': events,
        'can_view_stats': can_view_event_stats(request.user),
    }
    return render(request, 'events/calendar.html', context)


@user_passes_test(can_manage_events)
@require_http_methods(["GET"])
def event_list_view(request: HttpRequest) -> HttpResponse:
    """
    Vue pour lister tous les événements.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec la liste des événements
    """
    # Optimisation : charger uniquement les champs nécessaires pour la liste
    # Note: on ne peut pas utiliser only() avec select_related('adresse')
    # car only() défère tous les champs non listés, y compris la relation adresse
    events = Event.objects.select_related(
        'createur'
    ).prefetch_related(
        'secteurs'
    ).only(
        'id', 'titre', 'lieu', 'date_debut', 'date_fin',
        'couleur_calendrier', 'createur__email', 'createur__first_name',
        'createur__last_name'
    ).order_by('-date_debut')
    
    # Filtres
    secteur_id = request.GET.get('secteur')
    if secteur_id:
        try:
            events = events.filter(secteurs__id=int(secteur_id))
        except ValueError:
            pass
    
    date_debut = request.GET.get('date_debut')
    if date_debut:
        try:
            events = events.filter(date_debut__gte=date_debut)
        except ValueError:
            pass
    
    date_fin = request.GET.get('date_fin')
    if date_fin:
        try:
            events = events.filter(date_debut__lte=date_fin)
        except ValueError:
            pass
    
    # Pagination
    paginator = Paginator(events, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Récupérer tous les secteurs pour le filtre
    secteurs = get_secteurs_for_display()
    
    context = {
        'page_obj': page_obj,
        'events': page_obj,
        'secteurs': secteurs,
    }
    return render(request, 'events/list.html', context)


@user_passes_test(can_manage_events)
@require_http_methods(["GET"])
def event_detail_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Vue pour afficher les détails d'un événement.

    Args:
        request: Objet HttpRequest
        pk: Clé primaire de l'événement

    Returns:
        HttpResponse: Réponse HTTP avec les détails de l'événement
    """
    event = get_object_or_404(
        Event.objects.select_related(
            'createur', 'adresse'
        ).prefetch_related(
            'secteurs', 'fichiers'
        ),
        pk=pk
    )
    
    context = {
        'event': event,
    }
    return render(request, 'events/detail.html', context)


@user_passes_test(can_manage_events)
@require_http_methods(["GET", "POST"])
@rate_limit_uploads(max_uploads=10, window_seconds=60)
@transaction.non_atomic_requests
def event_create_view(request: HttpRequest) -> HttpResponse:
    """
    Vue pour créer un nouvel événement.
    
    Utilise @transaction.non_atomic_requests pour éviter les verrouillages SQLite
    lors de l'upload de fichiers volumineux. Les transactions sont gérées manuellement
    de manière granulaire.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec le formulaire ou redirection
    """
    if request.method == 'POST':
        # Créer une copie mutable de request.POST pour ajouter timezone si manquant
        post_data = request.POST.copy()
        if 'timezone' not in post_data or not post_data.get('timezone'):
            post_data['timezone'] = 'Europe/Paris'
        
        form = EventForm(post_data)
        
        if form.is_valid():
            # Sauvegarder l'événement dans une transaction courte
            with transaction.atomic():
                event = form.save(commit=False)
                # Assigner le créateur
                event.createur = request.user
                # Définir le timezone de l'utilisateur si non défini
                if not event.timezone:
                    # Utiliser le timezone par défaut ou celui de l'utilisateur
                    event.timezone = 'Europe/Paris'
                
                event.save()
                form.save_m2m()  # Sauvegarder les secteurs (ManyToMany)
            
            # Traiter les images EN DEHORS de la transaction principale
            # pour éviter les verrouillages SQLite pendant la compression
            images = request.FILES.getlist('images')
            if images:
                # Validation stricte de la taille côté serveur (sécurité supplémentaire)
                valid_images = []
                for img in images:
                    if img.size > MAX_FILE_SIZE:
                        messages.error(
                            request,
                            _('Le fichier "%(filename)s" est trop volumineux (max %(size)s MB).') % {
                                'filename': img.name,
                                'size': MAX_FILE_SIZE // (1024 * 1024)
                            }
                        )
                        continue
                    valid_images.append(img)
                
                # Limiter à 5 images
                images = valid_images[:5]
                
                # Compter les images existantes pour la numérotation
                # Utiliser count() car on a besoin du nombre exact pour la numérotation
                existing_images_count = event.fichiers.filter(type_fichier='image').count()
                
                # Traiter les images avec la fonction factorisée
                process_event_images(event, images, existing_images_count)
            
            # Recalculer la couleur après l'association des secteurs
            # dans une transaction courte
            with transaction.atomic():
                event.refresh_from_db()
                event.couleur_calendrier = event._calculate_calendar_color()
                event.save(update_fields=['couleur_calendrier'])
            
            # Invalider les caches
            cache.delete('event_timeline_recent')
            cache.delete('event_calendar_all')
            cache.delete('event_stats_view')  # Invalider le cache des stats
            
            logger.info(f'Événement créé: {event.titre} par {request.user.email}')
            messages.success(
                request,
                _('L\'événement "%(titre)s" a été créé avec succès.') % {'titre': event.titre}
            )
            return redirect('events:detail', pk=event.pk)
    else:
        form = EventForm()
        # Pré-remplir le timezone avec celui de l'utilisateur
        form.fields['timezone'].initial = 'Europe/Paris'
    
    # Récupérer tous les secteurs pour l'affichage
    secteurs = get_secteurs_for_display()
    
    context = {
        'form': form,
        'secteurs': secteurs,
    }
    return render(request, 'events/create.html', context)


@user_passes_test(can_manage_events)
@require_http_methods(["GET", "POST"])
@rate_limit_uploads(max_uploads=10, window_seconds=60)
@transaction.non_atomic_requests
def event_update_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Vue pour modifier un événement existant.
    
    Utilise @transaction.non_atomic_requests pour éviter les verrouillages SQLite
    lors de l'upload de fichiers volumineux. Les transactions sont gérées manuellement
    de manière granulaire.

    Args:
        request: Objet HttpRequest
        pk: Clé primaire de l'événement

    Returns:
        HttpResponse: Réponse HTTP avec le formulaire ou redirection
    """
    event = get_object_or_404(
        Event.objects.select_related('createur', 'adresse'),
        pk=pk
    )
    
    # Vérifier que l'utilisateur peut modifier cet événement
    # (créateur ou superuser)
    if not request.user.is_superuser and event.createur != request.user:
        messages.error(request, _('Vous n\'avez pas la permission de modifier cet événement.'))
        return redirect('events:detail', pk=event.pk)
    
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            # Sauvegarder l'événement dans une transaction courte
            with transaction.atomic():
                event = form.save()
                form.save_m2m()  # Sauvegarder les secteurs
            
            # Traiter les images EN DEHORS de la transaction principale
            # pour éviter les verrouillages SQLite pendant la compression
            images = request.FILES.getlist('images')
            if images:
                # Validation stricte de la taille côté serveur (sécurité supplémentaire)
                valid_images = []
                for img in images:
                    if img.size > MAX_FILE_SIZE:
                        messages.error(
                            request,
                            _('Le fichier "%(filename)s" est trop volumineux (max %(size)s MB).') % {
                                'filename': img.name,
                                'size': MAX_FILE_SIZE // (1024 * 1024)
                            }
                        )
                        continue
                    valid_images.append(img)
                
                # Compter les images existantes
                # Utiliser count() car on a besoin du nombre exact pour limiter à 5
                existing_images_count = event.fichiers.filter(type_fichier='image').count()
                # Limiter le total à 5 images
                max_new_images = min(5 - existing_images_count, len(valid_images))
                images = valid_images[:max_new_images]
                
                # Traiter les images avec la fonction factorisée
                process_event_images(event, images, existing_images_count)
            
            # Recalculer la couleur après l'association des secteurs
            # dans une transaction courte
            with transaction.atomic():
                event.refresh_from_db()
                event.couleur_calendrier = event._calculate_calendar_color()
                event.save(update_fields=['couleur_calendrier'])
            
            # Invalider les caches
            cache.delete('event_timeline_recent')
            cache.delete('event_calendar_all')
            cache.delete('event_stats_view')  # Invalider le cache des stats
            # Invalider aussi le cache spécifique au secteur si l'événement a des secteurs
            # Précharger les secteurs pour éviter N+1 queries
            secteurs_list = list(event.secteurs.all())
            for secteur in secteurs_list:
                cache.delete(f'event_calendar_{secteur.id}')
            
            logger.info(f'Événement modifié: {event.titre} par {request.user.email}')
            messages.success(
                request,
                _('L\'événement "%(titre)s" a été modifié avec succès.') % {'titre': event.titre}
            )
            return redirect('events:detail', pk=event.pk)
    else:
        form = EventForm(instance=event)
    
    # Récupérer tous les secteurs pour l'affichage
    secteurs = get_secteurs_for_display()
    
    context = {
        'form': form,
        'event': event,
        'secteurs': secteurs,
    }
    return render(request, 'events/update.html', context)


@user_passes_test(can_manage_events)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def event_delete_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Vue pour supprimer un événement.

    Args:
        request: Objet HttpRequest
        pk: Clé primaire de l'événement

    Returns:
        HttpResponse: Réponse HTTP avec confirmation ou redirection
    """
    event = get_object_or_404(
        Event.objects.select_related('createur'),
        pk=pk
    )
    
    # Vérifier que l'utilisateur peut supprimer cet événement
    if not request.user.is_superuser and event.createur != request.user:
        messages.error(request, _('Vous n\'avez pas la permission de supprimer cet événement.'))
        return redirect('events:detail', pk=event.pk)
    
    if request.method == 'POST':
        titre = event.titre
        # Récupérer les secteurs avant suppression pour invalider le cache
        secteurs_ids = list(event.secteurs.values_list('id', flat=True))
        event.delete()
        
        # Invalider les caches
        cache.delete('event_timeline_recent')
        cache.delete('event_calendar_all')
        cache.delete('event_stats_view')  # Invalider le cache des stats
        for secteur_id in secteurs_ids:
            cache.delete(f'event_calendar_{secteur_id}')
        
        logger.info(f'Événement supprimé: {titre} par {request.user.email}')
        messages.success(
            request,
            _('L\'événement "%(titre)s" a été supprimé avec succès.') % {'titre': titre}
        )
        return redirect('events:calendar')
    
    context = {
        'event': event,
    }
    return render(request, 'events/delete.html', context)


@user_passes_test(can_manage_events)
@require_http_methods(["GET"])
def event_timeline_view(request: HttpRequest) -> HttpResponse:
    """
    Vue optimisée pour afficher la timeline des événements.
    
    Utilise le cache pour optimiser les performances.
    
    Optimisations :
    - select_related pour ForeignKey/OneToOne
    - prefetch_related pour ManyToMany/Reverse FK
    - only() pour charger uniquement les champs nécessaires
    - Pré-calcul de tous les formats dans la vue
    
    Args:
        request: Objet HttpRequest
    
    Returns:
        HttpResponse: Réponse HTTP avec la timeline
    """
    # Mapping des jours et mois en français (toujours utiliser pour éviter les problèmes d'encodage)
    JOURS_FR = {
        'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
        'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi',
        'Sunday': 'Dimanche'
    }
    MOIS_FR = {
        'January': 'janvier', 'February': 'février', 'March': 'mars',
        'April': 'avril', 'May': 'mai', 'June': 'juin',
        'July': 'juillet', 'August': 'août', 'September': 'septembre',
        'October': 'octobre', 'November': 'novembre', 'December': 'décembre'
    }
    
    # Une seule requête optimisée avec limite pour éviter de charger trop de données
    # Limiter à TIMELINE_EVENTS_LIMIT événements récents pour optimiser les performances
    events = Event.objects.select_related(
        'createur', 'adresse'
    ).prefetch_related(
        'secteurs', 'fichiers'
    ).only(
        'id', 'titre', 'description', 'lieu', 'date_debut', 'date_fin',
        'couleur_calendrier', 'created_at',
        'demande_validation_dga', 'demande_validation_dgs',
        'statut_validation_dga', 'statut_validation_dgs',
        'createur__id', 'createur__first_name', 'createur__last_name', 'createur__email',
        'adresse__ville', 'adresse__code_postal', 'adresse__rue'
    ).order_by('-date_debut')[:TIMELINE_EVENTS_LIMIT]
    
    # Grouper efficacement en Python
    timeline_data = defaultdict(lambda: {'month_name': '', 'count': 0, 'dates': defaultdict(list)})
    
    for event in events:
        month_key = event.date_debut.strftime('%Y-%m')
        date_key = event.date_debut.date().isoformat()
        
        # Calculer le nom du mois une seule fois par mois
        if not timeline_data[month_key]['month_name']:
            # Toujours utiliser le mapping manuel pour éviter les problèmes d'encodage
            month_en = event.date_debut.strftime('%B')
            month_fr = MOIS_FR.get(month_en, month_en)
            # Capitaliser correctement (première lettre en majuscule)
            month_fr_capitalized = month_fr.capitalize() if month_fr else month_en
            timeline_data[month_key]['month_name'] = f"{month_fr_capitalized} {event.date_debut.year}"
        
        # Pré-calculer toutes les données nécessaires
        createur_nom = event.createur.get_full_name() or event.createur.email
        
        # Formater le jour de la semaine - toujours utiliser le mapping manuel
        day_en = event.date_debut.strftime('%A')
        day_name = JOURS_FR.get(day_en, day_en)
        
        # Déterminer si c'est une création (même jour que created_at)
        is_creation = (
            event.date_debut.date() == event.created_at.date() if event.created_at else False
        )
        
        # Déterminer si l'événement est passé
        now = timezone.now()
        if event.date_fin:
            is_past = event.date_fin < now
        else:
            is_past = event.date_debut < now
        
        event_data = {
            'event': event,
            'day_name': day_name,
            'date_formatted': event.date_debut.strftime('%d/%m/%Y'),
            'heure_debut': event.date_debut.strftime('%H:%M'),
            'createur_nom': createur_nom,
            'lieu_display': event.lieu or (event.adresse.ville if event.adresse else ''),
            'is_creation': is_creation,
            'is_past': is_past,
        }
        
        # Ajouter l'heure de fin si présente
        if event.date_fin:
            event_data['date_fin_formatted'] = event.date_fin.strftime('%d/%m/%Y')
            event_data['heure_fin'] = event.date_fin.strftime('%H:%M')
        
        timeline_data[month_key]['dates'][date_key].append(event_data)
        timeline_data[month_key]['count'] += 1
    
    # Convertir en structure ordonnée pour le template
    timeline_months = []
    for month_key in sorted(timeline_data.keys(), reverse=True):
        month_data = timeline_data[month_key]
        dates_list = []
        for date_key in sorted(month_data['dates'].keys(), reverse=True):
            # Parser la date depuis la clé ISO
            date_parts = date_key.split('-')
            date_obj = timezone.datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2])).date()
            dates_list.append({
                'date': date_key,
                'day': date_obj.day,
                'day_name': month_data['dates'][date_key][0]['day_name'],
                'events': month_data['dates'][date_key]
            })
        timeline_months.append({
            'key': month_key,
            'name': month_data['month_name'],
            'count': month_data['count'],
            'dates': dates_list
        })
    
    context = {
        'timeline_months': timeline_months,
    }
    return render(request, 'events/timeline.html', context)


@user_passes_test(can_manage_events)
@require_http_methods(["GET"])
def my_events_view(request: HttpRequest) -> HttpResponse:
    """
    Vue pour afficher les événements de l'utilisateur connecté.
    
    Affiche les événements futurs OU les événements passés avec une demande de validation.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec la liste des événements de l'utilisateur
    """
    from django.db.models import Q

    now = timezone.now()

    # Événements de l'utilisateur qui sont:
    # - Futurs (date_debut >= maintenant)
    # - OU passés avec une demande de validation (pour voir l'historique)
    events = Event.objects.filter(
        createur=request.user
    ).filter(
        Q(date_debut__gte=now) |
        Q(demande_validation_dga=True) |
        Q(demande_validation_dgs=True)
    ).select_related(
        'createur', 'adresse'
    ).prefetch_related(
        'secteurs'
    ).order_by('-date_debut')

    # Récupérer tous les secteurs pour le filtre
    secteurs = get_secteurs_for_display()

    context = {
        'events': events,
        'secteurs': secteurs,
        'is_my_events': True,
    }
    return render(request, 'events/my_events.html', context)


@user_passes_test(can_manage_events)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def event_validate_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Vue pour valider ou refuser un événement (DGA/DGS uniquement).

    Args:
        request: Objet HttpRequest
        pk: Clé primaire de l'événement

    Returns:
        HttpResponse: Réponse HTTP avec le formulaire ou redirection
    """
    event = get_object_or_404(
        Event.objects.select_related('createur', 'adresse'),
        pk=pk
    )

    # Vérifier que l'utilisateur peut valider
    user_is_dga = is_dga(request.user)
    user_is_dgs = is_dgs(request.user)

    if not user_is_dga and not user_is_dgs:
        messages.error(request, _('Vous n\'avez pas la permission de valider cet événement.'))
        return redirect('events:detail', pk=event.pk)

    # Déterminer quel type de validation l'utilisateur peut faire
    can_validate_dga = user_is_dga and event.demande_validation_dga and event.statut_validation_dga == 'en_attente'
    can_validate_dgs = user_is_dgs and event.demande_validation_dgs and event.statut_validation_dgs == 'en_attente'

    if request.method == 'POST':
        action = request.POST.get('action')  # 'valider' ou 'refuser'
        validation_type = request.POST.get('validation_type')  # 'dga' ou 'dgs'
        commentaire = request.POST.get('commentaire', '').strip()

        now = timezone.now()

        if validation_type == 'dga' and can_validate_dga:
            if action == 'valider':
                event.statut_validation_dga = 'valide'
                messages.success(request, _('L\'événement a été validé par le DGA.'))
            elif action == 'refuser':
                event.statut_validation_dga = 'refuse'
                messages.warning(request, _('L\'événement a été refusé par le DGA.'))
            event.date_validation_dga = now
            event.validateur_dga = request.user
            event.commentaire_validation_dga = commentaire if commentaire else None
            event.save()

        elif validation_type == 'dgs' and can_validate_dgs:
            if action == 'valider':
                event.statut_validation_dgs = 'valide'
                messages.success(request, _('L\'événement a été validé par le DGS.'))
            elif action == 'refuser':
                event.statut_validation_dgs = 'refuse'
                messages.warning(request, _('L\'événement a été refusé par le DGS.'))
            event.date_validation_dgs = now
            event.validateur_dgs = request.user
            event.commentaire_validation_dgs = commentaire if commentaire else None
            event.save()

        else:
            messages.error(request, _('Action non autorisée.'))

        # Invalider le cache
        cache.delete('event_timeline_recent')
        cache.delete('event_calendar_all')
        cache.delete('event_stats_view')  # Invalider le cache des stats

        return redirect('events:detail', pk=event.pk)

    context = {
        'event': event,
        'can_validate_dga': can_validate_dga,
        'can_validate_dgs': can_validate_dgs,
        'user_is_dga': user_is_dga,
        'user_is_dgs': user_is_dgs,
    }
    return render(request, 'events/validate.html', context)

