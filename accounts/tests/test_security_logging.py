"""
Tests pour le service de logging de sécurité.
"""
import logging
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch

User = get_user_model()

class SecurityLoggingTest(TestCase):
    """
    Tests pour vérifier que les événements de sécurité sont loggés.
    """

    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='security_test@example.com',
            password='testpass123',
            email_verified=True
        )

    @patch('accounts.services.security_logger.logger')
    def test_login_success_logging(self, mock_logger):
        """Test que la connexion réussie est loggée."""
        data = {
            'email': 'security_test@example.com',
            'password': 'testpass123',
        }
        self.client.post(reverse('accounts:login'), data)
        
        # Vérifier que logger.info a été appelé avec CONNEXION_REUSSIE
        calls = [call.args[0] for call in mock_logger.info.call_args_list]
        self.assertTrue(any("CONNEXION_REUSSIE" in s for s in calls))

    @patch('accounts.services.security_logger.logger')
    def test_login_failed_logging(self, mock_logger):
        """Test que la connexion échouée est loggée."""
        data = {
            'email': 'security_test@example.com',
            'password': 'wrongpassword',
        }
        self.client.post(reverse('accounts:login'), data)
        
        # Vérifier que logger.warning a été appelé avec CONNEXION_ECHOUEE
        calls = [call.args[0] for call in mock_logger.warning.call_args_list]
        self.assertTrue(any("CONNEXION_ECHOUEE" in s for s in calls))

    @patch('accounts.services.security_logger.logger')
    def test_password_change_logging(self, mock_logger):
        """Test que le changement de mot de passe est loggé."""
        self.client.force_login(self.user)
        data = {
            'old_password': 'testpass123',
            'new_password1': 'newpass123',
            'new_password2': 'newpass123',
        }
        self.client.post(reverse('accounts:password_change'), data)
        
        # Vérifier que logger.info a été appelé avec CHANGEMENT_MOT_DE_PASSE
        calls = [call.args[0] for call in mock_logger.info.call_args_list]
        self.assertTrue(any("CHANGEMENT_MOT_DE_PASSE" in s for s in calls))

    @patch('accounts.services.security_logger.logger')
    def test_account_creation_logging(self, mock_logger):
        """Test que la création de compte est loggée."""
        data = {
            'email': 'new_user@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        self.client.post(reverse('accounts:register'), data)
        
        # Vérifier que logger.info a été appelé avec COMPTE_CREE
        calls = [call.args[0] for call in mock_logger.info.call_args_list]
        self.assertTrue(any("COMPTE_CREE" in s for s in calls))
