"""
Configuration de l'admin Django pour l'application accounts.
"""
import csv
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _

User = get_user_model()


@admin.action(description='Activer les utilisateurs sélectionnés')
def make_active(modeladmin, request, queryset):
    """Action pour activer les utilisateurs sélectionnés."""
    queryset.update(is_active=True)


@admin.action(description='Désactiver les utilisateurs sélectionnés')
def make_inactive(modeladmin, request, queryset):
    """Action pour désactiver les utilisateurs sélectionnés."""
    queryset.update(is_active=False)


@admin.action(description='Promouvoir en administrateur')
def make_staff(modeladmin, request, queryset):
    """Action pour promouvoir les utilisateurs en administrateurs."""
    queryset.update(is_staff=True)


@admin.action(description='Rétrograder des administrateurs')
def remove_staff(modeladmin, request, queryset):
    """Action pour rétrograder les administrateurs."""
    queryset.update(is_staff=False)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Configuration de l'admin pour le modèle User personnalisé.
    """
    list_display = [
        'email',
        'first_name',
        'last_name',
        'is_active',
        'is_staff',
        'email_verified',
        'date_joined',
    ]
    list_filter = [
        'is_active',
        'is_staff',
        'is_superuser',
        'email_verified',
        'secteurs',
        'date_joined',
    ]
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    readonly_fields = ['date_joined', 'last_login']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (
            _('Informations personnelles'),
            {'fields': ('first_name', 'last_name')}
        ),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            }
        ),
        (
            _('Secteurs'),
            {
                'fields': ('secteurs',),
                'classes': ('collapse',)
            }
        ),
        (
            _('Vérification email'),
            {'fields': ('email_verified',)}
        ),
        (
            _('Préférences de notifications'),
            {
                'fields': (
                    'notify_welcome_email',
                    'notify_password_change',
                    'notify_new_login',
                    'notify_security_alerts',
                ),
                'classes': ('collapse',)
            }
        ),
        (
            _('Dates importantes'),
            {'fields': ('date_joined', 'last_login')}
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'password1', 'password2'),
            },
        ),
    )

    actions = [
        make_active,
        make_inactive,
        make_staff,
        remove_staff,
        'export_as_csv',
    ]

    def export_as_csv(self, request, queryset):
        """
        Exporte les utilisateurs sélectionnés en CSV.

        Args:
            request: Objet HttpRequest
            queryset: QuerySet des utilisateurs sélectionnés

        Returns:
            HttpResponse: Réponse HTTP avec le fichier CSV
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            f'attachment; filename="users_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        )

        writer = csv.writer(response)
        writer.writerow([
            'Email',
            'Prénom',
            'Nom',
            'Actif',
            'Staff',
            'Superuser',
            'Email vérifié',
            'Date d\'inscription',
        ])

        # Optimiser avec only() et iterator() pour les grandes listes
        optimized_queryset = queryset.only(
            'email', 'first_name', 'last_name', 'is_active',
            'is_staff', 'is_superuser', 'email_verified', 'date_joined'
        )
        for user in optimized_queryset.iterator():
            writer.writerow([
                user.email,
                user.first_name,
                user.last_name,
                'Oui' if user.is_active else 'Non',
                'Oui' if user.is_staff else 'Non',
                'Oui' if user.is_superuser else 'Non',
                'Oui' if user.email_verified else 'Non',
                user.date_joined.strftime('%d/%m/%Y %H:%M:%S'),
            ])

        return response

    export_as_csv.short_description = _('Exporter les utilisateurs sélectionnés en CSV')

    def changelist_view(self, request, extra_context=None):
        """
        Ajoute des statistiques à la vue de liste.

        Args:
            request: Objet HttpRequest
            extra_context: Contexte supplémentaire

        Returns:
            HttpResponse: Réponse HTTP avec les statistiques
        """
        extra_context = extra_context or {}

        # Optimiser les statistiques avec une seule requête annotée
        now = timezone.now()
        start_of_month = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # Utiliser annotate pour calculer toutes les stats en une requête
        stats = User.objects.aggregate(
            total_users=Count('id'),
            active_users=Count('id', filter=Q(is_active=True)),
            verified_users=Count('id', filter=Q(email_verified=True)),
            new_users_this_month=Count(
                'id', filter=Q(date_joined__gte=start_of_month)
            ),
        )

        extra_context['stats'] = stats

        return super().changelist_view(request, extra_context=extra_context)
