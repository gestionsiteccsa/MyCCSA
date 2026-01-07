"""
Tests de l'application accounts.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from .utils import (
    generate_verification_token,
    generate_password_reset_token,
    is_verification_token_valid,
    is_password_reset_token_valid,
    is_first_user,
)

User = get_user_model()


class UserModelTest(TestCase):
    """
    Tests pour le modèle User.
    """
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_user_str(self):
        """Test la méthode __str__ du modèle."""
        self.assertEqual(str(self.user), 'test@example.com')

    def test_user_get_full_name(self):
        """Test la méthode get_full_name."""
        self.assertEqual(self.user.get_full_name(), 'Test User')

    def test_user_get_short_name(self):
        """Test la méthode get_short_name."""
        self.assertEqual(self.user.get_short_name(), 'Test')

    def test_user_email_unique(self):
        """Test que l'email est unique."""
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='test@example.com',
                password='testpass123'
            )

    def test_first_user_becomes_superadmin(self):
        """Test que le premier utilisateur devient superadmin."""
        # Supprimer tous les utilisateurs
        User.objects.all().delete()

        # Créer le premier utilisateur
        first_user = User.objects.create_user(
            email='first@example.com',
            password='testpass123'
        )

        # Vérifier qu'il est superadmin
        self.assertTrue(first_user.is_superuser)
        self.assertTrue(first_user.is_staff)
        self.assertTrue(first_user.email_verified)


class RegistrationTest(TestCase):
    """
    Tests pour l'inscription.
    """
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = Client()
        self.register_url = reverse('accounts:register')

    def test_register_page_loads(self):
        """Test que la page d'inscription se charge."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_register_success(self):
        """Test une inscription réussie."""
        data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 302)  # Redirection
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_register_duplicate_email(self):
        """Test qu'on ne peut pas s'inscrire avec un email existant."""
        User.objects.create_user(
            email='existing@example.com',
            password='testpass123'
        )
        data = {
            'email': 'existing@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response, 'form', 'email',
            'Un compte avec cette adresse email existe déjà.'
        )

    def test_register_invalid_email(self):
        """Test inscription avec email invalide."""
        data = {
            'email': 'invalid-email',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    def test_register_password_mismatch(self):
        """Test inscription avec mots de passe différents."""
        data = {
            'email': 'newuser@example.com',
            'password1': 'testpass123',
            'password2': 'differentpass',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    def test_register_short_password(self):
        """Test inscription avec mot de passe trop court."""
        data = {
            'email': 'newuser@example.com',
            'password1': 'short',
            'password2': 'short',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    def test_register_authenticated_user_redirect(self):
        """Test redirection si utilisateur déjà connecté."""
        user = User.objects.create_user(
            email='loggedin@example.com',
            password='testpass123',
            email_verified=True
        )
        self.client.force_login(user)
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('accounts:profile'))


class LoginTest(TestCase):
    """
    Tests pour la connexion.
    """
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = Client()
        self.login_url = reverse('accounts:login')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            email_verified=True
        )

    def test_login_page_loads(self):
        """Test que la page de connexion se charge."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_login_success(self):
        """Test une connexion réussie."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 302)  # Redirection
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_invalid_credentials(self):
        """Test une connexion avec des identifiants invalides."""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_inactive_user(self):
        """Test connexion utilisateur inactif."""
        User.objects.create_user(
            email='inactive@example.com',
            password='testpass123',
            email_verified=True,
            is_active=False
        )
        data = {
            'email': 'inactive@example.com',
            'password': 'testpass123',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_unverified_email(self):
        """Test connexion email non vérifié."""
        User.objects.create_user(
            email='unverified@example.com',
            password='testpass123',
            email_verified=False
        )
        data = {
            'email': 'unverified@example.com',
            'password': 'testpass123',
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_remember_me(self):
        """Test connexion avec 'remember me'."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'remember_me': True,
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.wsgi_request.session.get_expiry_age(), 1209600)

    def test_login_next_redirect(self):
        """Test redirection après connexion avec paramètre next."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123',
        }
        next_url = reverse('accounts:profile')
        response = self.client.post(
            f'{self.login_url}?next={next_url}', data
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, next_url)

    def test_login_authenticated_user_redirect(self):
        """Test redirection si utilisateur déjà connecté."""
        self.client.force_login(self.user)
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('accounts:profile'))


class EmailVerificationTest(TestCase):
    """
    Tests pour la vérification d'email.
    """
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            email_verified=False
        )
        self.token = generate_verification_token()
        self.user.email_verification_token = self.token
        self.user.email_verification_sent_at = timezone.now()
        self.user.save()

    def test_verify_email_success(self):
        """Test une vérification d'email réussie."""
        url = reverse('accounts:verify_email', kwargs={'token': self.token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirection
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_verify_email_invalid_token(self):
        """Test une vérification avec un token invalide."""
        url = reverse('accounts:verify_email', kwargs={'token': 'invalid_token'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirection vers login

    def test_verify_email_expired_token(self):
        """Test vérification avec token expiré."""
        from datetime import timedelta
        self.user.email_verification_sent_at = (
            timezone.now() - timedelta(hours=25)
        )
        self.user.save()
        url = reverse('accounts:verify_email', kwargs={'token': self.token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)

    def test_verify_email_already_verified(self):
        """Test vérification email déjà vérifié."""
        self.user.email_verified = True
        self.user.save()
        url = reverse('accounts:verify_email', kwargs={'token': self.token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


class PasswordResetTest(TestCase):
    """
    Tests pour la réinitialisation de mot de passe.
    """
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            email_verified=True
        )

    def test_password_reset_request_page_loads(self):
        """Test que la page de demande de réinitialisation se charge."""
        url = reverse('accounts:password_reset')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/password_reset.html')

    def test_password_reset_request_success(self):
        """Test une demande de réinitialisation réussie."""
        url = reverse('accounts:password_reset')
        data = {'email': 'test@example.com'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirection
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.password_reset_token)

    def test_password_reset_request_nonexistent_email(self):
        """Test demande réinitialisation avec email inexistant."""
        url = reverse('accounts:password_reset')
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(url, data)
        # Ne doit pas révéler que l'email n'existe pas
        self.assertEqual(response.status_code, 302)

    def test_password_reset_request_invalid_form(self):
        """Test demande réinitialisation avec formulaire invalide."""
        url = reverse('accounts:password_reset')
        data = {'email': 'invalid-email'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())


class ProfileTest(TestCase):
    """
    Tests pour le profil utilisateur.
    """
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            email_verified=True
        )
        self.client.force_login(self.user)

    def test_profile_page_loads(self):
        """Test que la page de profil se charge."""
        url = reverse('accounts:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')

    def test_profile_edit_success(self):
        """Test une modification de profil réussie."""
        url = reverse('accounts:profile_edit')
        data = {
            'email': 'newemail@example.com',
            'first_name': 'New',
            'last_name': 'Name',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirection
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')
        self.assertEqual(self.user.first_name, 'New')

    def test_profile_edit_invalid_form(self):
        """Test modification profil avec formulaire invalide."""
        url = reverse('accounts:profile_edit')
        data = {
            'email': 'invalid-email',
            'first_name': 'New',
            'last_name': 'Name',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    def test_profile_edit_duplicate_email(self):
        """Test modification profil avec email déjà utilisé."""
        User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            email_verified=True
        )
        url = reverse('accounts:profile_edit')
        data = {
            'email': 'other@example.com',
            'first_name': 'New',
            'last_name': 'Name',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    def test_profile_edit_unauthenticated(self):
        """Test modification profil sans être connecté."""
        self.client.logout()
        url = reverse('accounts:profile_edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_password_change_page_loads(self):
        """Test que la page de changement de mot de passe se charge."""
        url = reverse('accounts:password_change')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/password_change.html')

    def test_password_change_success(self):
        """Test changement de mot de passe réussi."""
        url = reverse('accounts:password_change')
        data = {
            'old_password': 'testpass123',
            'new_password1': 'newpass123',
            'new_password2': 'newpass123',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))

    def test_password_change_wrong_old_password(self):
        """Test changement avec ancien mot de passe incorrect."""
        url = reverse('accounts:password_change')
        data = {
            'old_password': 'wrongpassword',
            'new_password1': 'newpass123',
            'new_password2': 'newpass123',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    def test_password_change_short_password(self):
        """Test changement avec nouveau mot de passe trop court."""
        url = reverse('accounts:password_change')
        data = {
            'old_password': 'testpass123',
            'new_password1': 'short',
            'new_password2': 'short',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    def test_password_change_unauthenticated(self):
        """Test changement mot de passe sans être connecté."""
        self.client.logout()
        url = reverse('accounts:password_change')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class NotificationSettingsTest(TestCase):
    """
    Tests pour les préférences de notifications.
    """
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            email_verified=True
        )
        self.client.force_login(self.user)

    def test_notifications_settings_page_loads(self):
        """Test que la page de préférences se charge."""
        url = reverse('accounts:notifications_settings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/notifications_settings.html')

    def test_notifications_settings_update(self):
        """Test la mise à jour des préférences."""
        url = reverse('accounts:notifications_settings')
        data = {
            'notify_welcome_email': False,
            'notify_password_change': True,
            'notify_new_login': False,
            'notify_security_alerts': True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirection
        self.user.refresh_from_db()
        self.assertFalse(self.user.notify_welcome_email)
        self.assertTrue(self.user.notify_password_change)
        self.assertFalse(self.user.notify_new_login)
        self.assertTrue(self.user.notify_security_alerts)

    def test_notifications_settings_unauthenticated(self):
        """Test préférences notifications sans être connecté."""
        self.client.logout()
        url = reverse('accounts:notifications_settings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class UtilsTest(TestCase):
    """
    Tests pour les fonctions utilitaires.
    """
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_generate_verification_token(self):
        """Test la génération d'un token de vérification."""
        token = generate_verification_token()
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)

    def test_generate_password_reset_token(self):
        """Test la génération d'un token de réinitialisation."""
        token = generate_password_reset_token()
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)

    def test_is_first_user(self):
        """Test la détection du premier utilisateur."""
        User.objects.all().delete()
        self.assertTrue(is_first_user())
        User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertFalse(is_first_user())

    def test_is_verification_token_valid_expired(self):
        """Test validation token expiré."""
        from datetime import timedelta
        token = generate_verification_token()
        self.user.email_verification_token = token
        self.user.email_verification_sent_at = (
            timezone.now() - timedelta(hours=25)
        )
        self.user.save()
        self.assertFalse(
            is_verification_token_valid(self.user, token, expiration_hours=24)
        )

    def test_is_verification_token_valid_invalid(self):
        """Test validation token invalide."""
        token = generate_verification_token()
        self.user.email_verification_token = token
        self.user.email_verification_sent_at = timezone.now()
        self.user.save()
        self.assertFalse(
            is_verification_token_valid(self.user, 'wrong_token')
        )

    def test_is_password_reset_token_valid_expired(self):
        """Test validation token réinitialisation expiré."""
        from datetime import timedelta
        token = generate_password_reset_token()
        self.user.password_reset_token = token
        self.user.password_reset_sent_at = (
            timezone.now() - timedelta(hours=2)
        )
        self.user.save()
        self.assertFalse(
            is_password_reset_token_valid(
                self.user, token, expiration_hours=1
            )
        )

    def test_is_password_reset_token_valid_invalid(self):
        """Test validation token réinitialisation invalide."""
        token = generate_password_reset_token()
        self.user.password_reset_token = token
        self.user.password_reset_sent_at = timezone.now()
        self.user.save()
        self.assertFalse(
            is_password_reset_token_valid(self.user, 'wrong_token')
        )

    def test_get_client_ip(self):
        """Test récupération IP client."""
        from django.test import RequestFactory
        from .utils import get_client_ip
        factory = RequestFactory()
        request = factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')

    def test_get_client_ip_x_forwarded_for(self):
        """Test récupération IP avec X-Forwarded-For."""
        from django.test import RequestFactory
        from .utils import get_client_ip
        factory = RequestFactory()
        request = factory.get('/', HTTP_X_FORWARDED_FOR='10.0.0.1,192.168.1.1')
        ip = get_client_ip(request)
        self.assertEqual(ip, '10.0.0.1')


class LogoutTest(TestCase):
    """
    Tests pour la déconnexion.
    """
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            email_verified=True
        )
        self.client.force_login(self.user)

    def test_logout_success(self):
        """Test déconnexion réussie."""
        url = reverse('accounts:logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('accounts:login'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class TransactionTest(TestCase):
    """
    Tests pour les transactions atomiques.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client()

    def test_verify_email_view_atomic(self):
        """Test que verify_email_view est atomique."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            email_verified=False
        )
        token = generate_verification_token()
        user.email_verification_token = token
        user.email_verification_sent_at = timezone.now()
        user.save()

        url = reverse('accounts:verify_email', kwargs={'token': token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'email est vérifié (transaction réussie)
        user.refresh_from_db()
        self.assertTrue(user.email_verified)

    def test_password_reset_confirm_view_atomic(self):
        """Test que password_reset_confirm_view est atomique."""
        user = User.objects.create_user(
            email='test@example.com',
            password='oldpass123',
            email_verified=True
        )
        token = generate_password_reset_token()
        user.password_reset_token = token
        user.password_reset_sent_at = timezone.now()
        user.save()

        url = reverse(
            'accounts:password_reset_confirm',
            kwargs={'token': token}
        )
        data = {
            'new_password1': 'newpass123',
            'new_password2': 'newpass123',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # Vérifier que le mot de passe a été changé et le token supprimé
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpass123'))
        self.assertEqual(user.password_reset_token, '')
