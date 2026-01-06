"""
Fonctions utilitaires pour l'application dashboard.
"""
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


def get_dashboard_stats():
    """
    Récupère les statistiques pour le dashboard.

    Returns:
        dict: Dictionnaire contenant les statistiques
    """
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_week = now - timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    # Statistiques utilisateurs
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    verified_users = User.objects.filter(email_verified=True).count()
    new_users_this_month = User.objects.filter(date_joined__gte=start_of_month).count()
    new_users_this_week = User.objects.filter(date_joined__gte=start_of_week).count()

    # Statistiques secteurs
    try:
        from secteurs.models import Secteur
        total_secteurs = Secteur.objects.count()
        users_with_secteurs = User.objects.filter(secteurs__isnull=False).distinct().count()
        latest_secteurs = Secteur.objects.order_by('-created_at')[:5]
    except ImportError:
        total_secteurs = 0
        users_with_secteurs = 0
        latest_secteurs = []

    # Statistiques rôles
    try:
        from role.models import Role
        total_roles = Role.objects.count()
        users_with_roles = User.objects.filter(role__isnull=False).count()
        latest_roles = Role.objects.order_by('-created_at')[:5]
    except ImportError:
        total_roles = 0
        users_with_roles = 0
        latest_roles = []

    # Statistiques évènements (validation)
    try:
        from events.models import Event
        events_pending_dga = Event.objects.filter(statut_validation_dga='en_attente').count()
        events_pending_dgs = Event.objects.filter(statut_validation_dgs='en_attente').count()
        total_pending_validation = Event.objects.filter(
            Q(statut_validation_dga='en_attente') | Q(statut_validation_dgs='en_attente')
        ).distinct().count()
    except ImportError:
        events_pending_dga = 0
        events_pending_dgs = 0
        total_pending_validation = 0

    # Derniers utilisateurs inscrits
    latest_users = User.objects.select_related().order_by('-date_joined')[:5]

    return {
        'total_users': total_users,
        'active_users': active_users,
        'verified_users': verified_users,
        'new_users_this_month': new_users_this_month,
        'new_users_this_week': new_users_this_week,
        'total_secteurs': total_secteurs,
        'users_with_secteurs': users_with_secteurs,
        'total_roles': total_roles,
        'users_with_roles': users_with_roles,
        'events_pending_dga': events_pending_dga,
        'events_pending_dgs': events_pending_dgs,
        'total_pending_validation': total_pending_validation,
        'latest_users': latest_users,
        'latest_secteurs': latest_secteurs,
        'latest_roles': latest_roles,
    }




