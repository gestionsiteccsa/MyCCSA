"""
Tests pour les formulaires de l'application accounts.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.forms import (
    UserRegistrationForm,
    UserLoginForm,
    UserProfileEditForm,
    CustomPasswordChangeForm,
    PasswordResetRequestForm,
    PasswordResetConfirmForm,
    NotificationSettingsForm,
)

User = get_user_model()


class UserRegistrationFormTest(TestCase):
    """
    Tests pour le formulaire d'inscription.
    """
    def test_valid_form(self):
        """Test formulaire valide."""
        form_data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        """Test mots de passe différents."""
        form_data = {
            'email': 'newuser@example.com',
            'password1': 'testpass123',
            'password2': 'differentpass',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_duplicate_email(self):
        """Test email déjà utilisé."""
        User.objects.create_user(
            email='existing@example.com',
            password='testpass123'
        )
        form_data = {
            'email': 'existing@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_invalid_email(self):
        """Test email invalide."""
        form_data = {
            'email': 'invalid-email',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_save_user(self):
        """Test sauvegarde utilisateur."""
        form_data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertTrue(user.check_password('testpass123'))


class UserLoginFormTest(TestCase):
    """
    Tests pour le formulaire de connexion.
    """
    def test_valid_form(self):
        """Test formulaire valide."""
        form_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
        }
        form = UserLoginForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_email(self):
        """Test email invalide."""
        form_data = {
            'email': 'invalid-email',
            'password': 'testpass123',
        }
        form = UserLoginForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_remember_me(self):
        """Test case 'remember me'."""
        form_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'remember_me': True,
        }
        form = UserLoginForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.cleaned_data['remember_me'])


class UserProfileEditFormTest(TestCase):
    """
    Tests pour le formulaire d'édition de profil.
    """
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_valid_form(self):
        """Test formulaire valide."""
        form_data = {
            'email': 'newemail@example.com',
            'first_name': 'New',
            'last_name': 'Name',
        }
        form = UserProfileEditForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_duplicate_email(self):
        """Test email déjà utilisé par un autre utilisateur."""
        User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        form_data = {
            'email': 'other@example.com',
            'first_name': 'New',
            'last_name': 'Name',
        }
        form = UserProfileEditForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_same_email(self):
        """Test garder le même email."""
        form_data = {
            'email': 'test@example.com',
            'first_name': 'New',
            'last_name': 'Name',
        }
        form = UserProfileEditForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())


class PasswordResetConfirmFormTest(TestCase):
    """
    Tests pour le formulaire de confirmation de réinitialisation.
    """
    def test_valid_form(self):
        """Test formulaire valide."""
        form_data = {
            'new_password1': 'newpass123',
            'new_password2': 'newpass123',
        }
        form = PasswordResetConfirmForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        """Test mots de passe différents."""
        form_data = {
            'new_password1': 'newpass123',
            'new_password2': 'differentpass',
        }
        form = PasswordResetConfirmForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('new_password2', form.errors)


class NotificationSettingsFormTest(TestCase):
    """
    Tests pour le formulaire de préférences de notifications.
    """
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_valid_form(self):
        """Test formulaire valide."""
        form_data = {
            'notify_welcome_email': False,
            'notify_password_change': True,
            'notify_new_login': False,
            'notify_security_alerts': True,
        }
        form = NotificationSettingsForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_save_preferences(self):
        """Test sauvegarde des préférences."""
        form_data = {
            'notify_welcome_email': False,
            'notify_password_change': True,
            'notify_new_login': False,
            'notify_security_alerts': True,
        }
        form = NotificationSettingsForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        form.save()
        self.user.refresh_from_db()
        self.assertFalse(self.user.notify_welcome_email)
        self.assertTrue(self.user.notify_password_change)
