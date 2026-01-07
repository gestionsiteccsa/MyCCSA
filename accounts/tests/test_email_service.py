"""
Tests pour le service d'envoi d'emails.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core import mail
from accounts.services.email_service import EmailService

User = get_user_model()


class EmailServiceTest(TestCase):
    """
    Tests pour le service EmailService.
    """
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            email_verified=True
        )

    @patch('accounts.services.email_service.send_mail')
    @patch('accounts.services.email_service.render_to_string')
    def test_send_verification_email(self, mock_render, mock_send_mail):
        """Test envoi email de vérification."""
        mock_render.return_value = '<html>Verification</html>'
        mock_send_mail.return_value = True

        result = EmailService.send_verification_email(
            self.user, 'http://example.com/verify/token'
        )

        self.assertTrue(result)
        mock_send_mail.assert_called_once()

    @patch('accounts.services.email_service.send_mail')
    @patch('accounts.services.email_service.render_to_string')
    def test_send_welcome_email(self, mock_render, mock_send_mail):
        """Test envoi email de bienvenue."""
        mock_render.return_value = '<html>Welcome</html>'
        mock_send_mail.return_value = True

        result = EmailService.send_welcome_email(self.user)

        self.assertTrue(result)
        mock_send_mail.assert_called_once()

    @patch('accounts.services.email_service.send_mail')
    @patch('accounts.services.email_service.render_to_string')
    def test_send_welcome_email_preference_disabled(self, mock_render, mock_send_mail):
        """Test envoi email de bienvenue avec préférence désactivée."""
        self.user.notify_welcome_email = False
        self.user.save()

        result = EmailService.send_welcome_email(self.user)

        self.assertFalse(result)
        mock_send_mail.assert_not_called()

    @patch('accounts.services.email_service.send_mail')
    @patch('accounts.services.email_service.render_to_string')
    def test_send_password_reset_email(self, mock_render, mock_send_mail):
        """Test envoi email de réinitialisation."""
        mock_render.return_value = '<html>Reset</html>'
        mock_send_mail.return_value = True

        result = EmailService.send_password_reset_email(
            self.user, 'http://example.com/reset/token'
        )

        self.assertTrue(result)
        mock_send_mail.assert_called_once()

    @patch('accounts.services.email_service.send_mail')
    @patch('accounts.services.email_service.render_to_string')
    def test_send_password_change_email(self, mock_render, mock_send_mail):
        """Test envoi email de changement de mot de passe."""
        mock_render.return_value = '<html>Password Changed</html>'
        mock_send_mail.return_value = True

        result = EmailService.send_password_change_email(self.user)

        self.assertTrue(result)
        mock_send_mail.assert_called_once()

    @patch('accounts.services.email_service.send_mail')
    @patch('accounts.services.email_service.render_to_string')
    def test_send_password_change_email_preference_disabled(
        self, mock_render, mock_send_mail
    ):
        """Test envoi email changement mot de passe avec préférence désactivée."""
        self.user.notify_password_change = False
        self.user.save()

        result = EmailService.send_password_change_email(self.user)

        self.assertFalse(result)
        mock_send_mail.assert_not_called()

    @patch('accounts.services.email_service.send_mail')
    @patch('accounts.services.email_service.render_to_string')
    def test_send_new_login_email(self, mock_render, mock_send_mail):
        """Test envoi email de nouvelle connexion."""
        mock_render.return_value = '<html>New Login</html>'
        mock_send_mail.return_value = True

        result = EmailService.send_new_login_email(self.user, '192.168.1.1')

        self.assertTrue(result)
        mock_send_mail.assert_called_once()

    @patch('accounts.services.email_service.send_mail')
    @patch('accounts.services.email_service.render_to_string')
    def test_send_new_login_email_preference_disabled(
        self, mock_render, mock_send_mail
    ):
        """Test envoi email nouvelle connexion avec préférence désactivée."""
        self.user.notify_new_login = False
        self.user.save()

        result = EmailService.send_new_login_email(self.user, '192.168.1.1')

        self.assertFalse(result)
        mock_send_mail.assert_not_called()

    @patch('accounts.services.email_service.send_mail')
    @patch('accounts.services.email_service.render_to_string')
    def test_send_security_alert_email(self, mock_render, mock_send_mail):
        """Test envoi email d'alerte de sécurité."""
        mock_render.return_value = '<html>Security Alert</html>'
        mock_send_mail.return_value = True

        result = EmailService.send_security_alert_email(
            self.user, 'Suspicious activity detected', '192.168.1.1'
        )

        self.assertTrue(result)
        mock_send_mail.assert_called_once()

    @patch('accounts.services.email_service.send_mail')
    @patch('accounts.services.email_service.render_to_string')
    def test_send_security_alert_email_preference_disabled(
        self, mock_render, mock_send_mail
    ):
        """Test envoi email alerte sécurité avec préférence désactivée."""
        self.user.notify_security_alerts = False
        self.user.save()

        result = EmailService.send_security_alert_email(
            self.user, 'Suspicious activity detected', '192.168.1.1'
        )

        self.assertFalse(result)
        mock_send_mail.assert_not_called()

    @patch('accounts.services.email_service.send_mail')
    @patch('accounts.services.email_service.render_to_string')
    def test_send_email_failure(self, mock_render, mock_send_mail):
        """Test échec d'envoi d'email."""
        mock_render.return_value = '<html>Test</html>'
        mock_send_mail.side_effect = Exception('SMTP Error')

        result = EmailService.send_verification_email(
            self.user, 'http://example.com/verify/token'
        )

        self.assertFalse(result)
