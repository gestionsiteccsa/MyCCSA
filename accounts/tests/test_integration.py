"""
Tests d'intégration pour l'application accounts.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from accounts.utils import generate_verification_token, generate_password_reset_token

User = get_user_model()


class RegistrationWorkflowTest(TestCase):
    """
    Tests du workflow complet d'inscription.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client()

    def test_complete_registration_workflow(self):
        """Test workflow complet : inscription → vérification → connexion."""
        # Étape 1 : Inscription
        register_url = reverse('accounts:register')
        data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        response = self.client.post(register_url, data)
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'utilisateur existe mais n'est pas vérifié
        user = User.objects.get(email='newuser@example.com')
        self.assertFalse(user.email_verified)
        self.assertIsNotNone(user.email_verification_token)

        # Étape 2 : Vérification email
        verify_url = reverse(
            'accounts:verify_email',
            kwargs={'token': user.email_verification_token}
        )
        response = self.client.get(verify_url)
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'email est maintenant vérifié
        user.refresh_from_db()
        self.assertTrue(user.email_verified)
        self.assertEqual(user.email_verification_token, '')

        # Étape 3 : Connexion
        login_url = reverse('accounts:login')
        data = {
            'email': 'newuser@example.com',
            'password': 'testpass123',
        }
        response = self.client.post(login_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)


class PasswordResetWorkflowTest(TestCase):
    """
    Tests du workflow complet de réinitialisation de mot de passe.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='oldpass123',
            email_verified=True
        )

    def test_complete_password_reset_workflow(self):
        """Test workflow complet de réinitialisation."""
        # Étape 1 : Demande de réinitialisation
        reset_url = reverse('accounts:password_reset')
        data = {'email': 'test@example.com'}
        response = self.client.post(reset_url, data)
        self.assertEqual(response.status_code, 302)

        # Vérifier que le token a été généré
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.password_reset_token)

        # Étape 2 : Confirmation et nouveau mot de passe
        confirm_url = reverse(
            'accounts:password_reset_confirm',
            kwargs={'token': self.user.password_reset_token}
        )
        data = {
            'new_password1': 'newpass123',
            'new_password2': 'newpass123',
        }
        response = self.client.post(confirm_url, data)
        self.assertEqual(response.status_code, 302)

        # Vérifier que le mot de passe a été changé
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))
        self.assertEqual(self.user.password_reset_token, '')

        # Étape 3 : Connexion avec le nouveau mot de passe
        login_url = reverse('accounts:login')
        data = {
            'email': 'test@example.com',
            'password': 'newpass123',
        }
        response = self.client.post(login_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)


class PasswordChangeWorkflowTest(TestCase):
    """
    Tests du workflow complet de changement de mot de passe.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='oldpass123',
            email_verified=True
        )
        self.client.force_login(self.user)

    def test_complete_password_change_workflow(self):
        """Test workflow complet de changement de mot de passe."""
        # Changer le mot de passe
        change_url = reverse('accounts:password_change')
        data = {
            'old_password': 'oldpass123',
            'new_password1': 'newpass123',
            'new_password2': 'newpass123',
        }
        response = self.client.post(change_url, data)
        self.assertEqual(response.status_code, 302)

        # Vérifier que le mot de passe a été changé
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))

        # Se déconnecter et se reconnecter avec le nouveau mot de passe
        logout_url = reverse('accounts:logout')
        self.client.post(logout_url)

        login_url = reverse('accounts:login')
        data = {
            'email': 'test@example.com',
            'password': 'newpass123',
        }
        response = self.client.post(login_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)


class ProfileEditWorkflowTest(TestCase):
    """
    Tests du workflow de modification de profil.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Old',
            last_name='Name',
            email_verified=True
        )
        self.client.force_login(self.user)

    def test_complete_profile_edit_workflow(self):
        """Test workflow complet de modification de profil."""
        # Modifier le profil
        edit_url = reverse('accounts:profile_edit')
        data = {
            'email': 'newemail@example.com',
            'first_name': 'New',
            'last_name': 'Name',
        }
        response = self.client.post(edit_url, data)
        self.assertEqual(response.status_code, 302)

        # Vérifier que les modifications ont été sauvegardées
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')
        self.assertEqual(self.user.first_name, 'New')
        self.assertEqual(self.user.last_name, 'Name')

        # Vérifier que le profil affiche les nouvelles informations
        profile_url = reverse('accounts:profile')
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'newemail@example.com')
        self.assertContains(response, 'New')
        self.assertContains(response, 'Name')

