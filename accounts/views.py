"""
Vues de l'application accounts.
"""
import logging
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.http import HttpRequest, HttpResponse, Http404
from django.utils.translation import gettext_lazy as _

from .forms import (
    UserRegistrationForm,
    UserLoginForm,
    UserProfileEditForm,
    CustomPasswordChangeForm,
    PasswordResetRequestForm,
    PasswordResetConfirmForm,
    NotificationSettingsForm,
)
from .services.email_service import EmailService
from .services.security_logger import SecurityLogger
from .utils import (
    generate_verification_token,
    generate_password_reset_token,
    is_verification_token_valid,
    is_password_reset_token_valid,
    is_first_user,
    get_client_ip,
)

logger = logging.getLogger(__name__)
User = get_user_model()


@require_http_methods(["GET", "POST"])
@transaction.atomic
def register_view(request: HttpRequest) -> HttpResponse:
    """
    Vue d'inscription utilisateur.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec le formulaire d'inscription
    """
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Vérifier si c'est le premier utilisateur
            if is_first_user():
                user.is_superuser = True
                user.is_staff = True
                user.email_verified = True
                messages.success(
                    request,
                    _(
                        'Félicitations ! Vous êtes le premier utilisateur '
                        'et avez été automatiquement promu administrateur.'
                    )
                )
            else:
                # L'utilisateur est vérifié d'office
                user.email_verified = True

            user.save()

            # Log de sécurité
            SecurityLogger.log_account_created(user)

            # Envoyer l'email de bienvenue (si préférence activée)
            EmailService.send_welcome_email(user)

            messages.success(
                request,
                _('Votre compte a été créé avec succès. Vous pouvez maintenant vous connecter.')
            )
            return redirect('accounts:login')

    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    """
    Vue de connexion utilisateur.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec le formulaire de connexion
    """
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)

            user = authenticate(request, username=email, password=password)

            if user is not None:
                if not user.is_active:
                    messages.error(
                        request,
                        _('Votre compte a été désactivé.')
                    )
                    return render(request, 'accounts/login.html', {'form': form})

                if not user.email_verified:
                    messages.warning(
                        request,
                        _(
                            'Votre email n\'a pas été vérifié. '
                            'Vérifiez votre boîte de réception.'
                        )
                    )
                    return render(request, 'accounts/login.html', {'form': form})

                login(request, user)

                # Log de sécurité
                ip_address = get_client_ip(request)
                SecurityLogger.log_login_success(user, ip_address)

                # Configurer la durée de la session
                if not remember_me:
                    request.session.set_expiry(0)  # Session expire à la fermeture
                else:
                    request.session.set_expiry(1209600)  # 2 semaines

                # Envoyer l'email de nouvelle connexion (si préférence activée)
                ip_address = get_client_ip(request)
                EmailService.send_new_login_email(user, ip_address)

                messages.success(
                    request,
                    _('Vous êtes maintenant connecté.')
                )

                # Redirection après connexion
                next_url = request.GET.get('next', 'accounts:profile')
                return redirect(next_url)

            else:
                # Log de sécurité
                ip_address = get_client_ip(request)
                SecurityLogger.log_login_failed(email, ip_address)

                messages.error(
                    request,
                    _('Email ou mot de passe incorrect.')
                )

    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@require_http_methods(["GET"])
@transaction.atomic
def verify_email_view(
    request: HttpRequest, token: str
) -> HttpResponse:
    """
    Vue de vérification d'email.

    Args:
        request: Objet HttpRequest
        token: Token de vérification

    Returns:
        HttpResponse: Réponse HTTP de confirmation
    """
    try:
        user = User.objects.select_for_update().only(
            'id', 'email', 'email_verified', 'email_verification_token',
            'email_verification_sent_at'
        ).get(email_verification_token=token)
    except User.DoesNotExist:
        messages.error(
            request,
            _('Token de vérification invalide.')
        )
        return redirect('accounts:login')

    if user.email_verified:
        messages.info(
            request,
            _('Votre email a déjà été vérifié.')
        )
        return redirect('accounts:login')

    if not is_verification_token_valid(user, token):
        messages.error(
            request,
            _('Le token de vérification a expiré.')
        )
        return redirect('accounts:login')

    # Vérifier l'email
    user.email_verified = True
    user.email_verification_token = ''
    user.email_verification_sent_at = None
    user.save()

    messages.success(
        request,
        _('Votre email a été vérifié avec succès. Vous pouvez maintenant vous connecter.')
    )
    return redirect('accounts:login')


@require_http_methods(["GET", "POST"])
def password_reset_request_view(request: HttpRequest) -> HttpResponse:
    """
    Vue de demande de réinitialisation de mot de passe.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec le formulaire de demande
    """
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.only(
                    'id', 'email', 'password_reset_token',
                    'password_reset_sent_at'
                ).get(email=email)
                token = generate_password_reset_token()
                user.password_reset_token = token
                user.password_reset_sent_at = timezone.now()
                user.save()

                # Log de sécurité
                SecurityLogger.log_password_reset_request(email)

                reset_url = request.build_absolute_uri(
                    reverse(
                        'accounts:password_reset_confirm',
                        kwargs={'token': token}
                    )
                )
                EmailService.send_password_reset_email(user, reset_url)

                messages.success(
                    request,
                    _(
                        'Si un compte existe avec cette adresse email, '
                        'vous recevrez un email avec les instructions.'
                    )
                )
            except User.DoesNotExist:
                # Ne pas révéler si l'email existe ou non
                messages.success(
                    request,
                    _(
                        'Si un compte existe avec cette adresse email, '
                        'vous recevrez un email avec les instructions.'
                    )
                )

            return redirect('accounts:login')

    else:
        form = PasswordResetRequestForm()

    return render(request, 'accounts/password_reset.html', {'form': form})


@require_http_methods(["GET", "POST"])
@transaction.atomic
def password_reset_confirm_view(
    request: HttpRequest, token: str
) -> HttpResponse:
    """
    Vue de confirmation de réinitialisation de mot de passe.

    Args:
        request: Objet HttpRequest
        token: Token de réinitialisation

    Returns:
        HttpResponse: Réponse HTTP avec le formulaire de réinitialisation
    """
    try:
        user = User.objects.select_for_update().only(
            'id', 'email', 'password_reset_token', 'password_reset_sent_at'
        ).get(password_reset_token=token)
    except User.DoesNotExist:
        messages.error(
            request,
            _('Token de réinitialisation invalide.')
        )
        return redirect('accounts:password_reset')

    # Vérifier l'expiration du token (1 heure)
    if not is_password_reset_token_valid(user, token, expiration_hours=1):
        messages.error(
            request,
            _('Le token de réinitialisation a expiré.')
        )
        return redirect('accounts:password_reset')

    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password1'])
            user.password_reset_token = ''
            user.password_reset_sent_at = None
            user.save()

            messages.success(
                request,
                _('Votre mot de passe a été réinitialisé avec succès.')
            )
            return redirect('accounts:login')

    else:
        form = PasswordResetConfirmForm()

    return render(
        request,
        'accounts/password_reset_confirm.html',
        {'form': form, 'token': token}
    )


@login_required
@require_http_methods(["GET"])
def profile_view(request: HttpRequest) -> HttpResponse:
    """
    Vue d'affichage du profil utilisateur.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec le profil de l'utilisateur
    """
    # Précharger les secteurs pour éviter N+1 queries
    user = User.objects.prefetch_related('secteurs').get(pk=request.user.pk)
    return render(request, 'accounts/profile.html', {'user': user})


@login_required
@require_http_methods(["GET", "POST"])
def profile_edit_view(request: HttpRequest) -> HttpResponse:
    """
    Vue d'édition du profil utilisateur.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec le formulaire d'édition
    """
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, instance=request.user, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                _('Votre profil a été mis à jour avec succès.')
            )
            return redirect('accounts:profile')

    else:
        form = UserProfileEditForm(instance=request.user, user=request.user)

    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
@require_http_methods(["GET", "POST"])
def password_change_view(request: HttpRequest) -> HttpResponse:
    """
    Vue de changement de mot de passe.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec le formulaire de changement
    """
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            # Log de sécurité
            SecurityLogger.log_password_change(request.user)
            # Envoyer l'email de notification (si préférence activée)
            EmailService.send_password_change_email(request.user)
            messages.success(
                request,
                _('Votre mot de passe a été modifié avec succès.')
            )
            return redirect('accounts:profile')

    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'accounts/password_change.html', {'form': form})


@login_required
@require_http_methods(["GET", "POST"])
def notifications_settings_view(request: HttpRequest) -> HttpResponse:
    """
    Vue de gestion des préférences de notifications.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Réponse HTTP avec le formulaire de préférences
    """
    if request.method == 'POST':
        form = NotificationSettingsForm(
            request.POST,
            instance=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(
                request,
                _('Vos préférences de notifications ont été mises à jour.')
            )
            return redirect('accounts:notifications_settings')

    else:
        form = NotificationSettingsForm(instance=request.user)

    return render(
        request,
        'accounts/notifications_settings.html',
        {'form': form}
    )


@login_required
@require_http_methods(["POST"])
def logout_view(request: HttpRequest) -> HttpResponse:
    """
    Vue de déconnexion utilisateur.

    Args:
        request: Objet HttpRequest

    Returns:
        HttpResponse: Redirection vers la page de connexion
    """
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, _('Vous avez été déconnecté avec succès.'))
    return redirect('accounts:login')
