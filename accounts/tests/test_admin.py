"""
Tests pour l'admin de l'application accounts.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q

User = get_user_model()


class UserAdminTest(TestCase):
    """
    Tests pour l'interface d'administration des utilisateurs.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.client.force_login(self.admin_user)
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            is_active=True
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            is_active=False
        )

    def test_admin_changelist_view(self):
        """Test que la liste des utilisateurs se charge."""
        url = reverse('admin:accounts_user_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_admin_changelist_statistics(self):
        """Test que les statistiques sont affichées."""
        url = reverse('admin:accounts_user_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Vérifier que les stats sont dans le contexte
        self.assertIn('stats', response.context)

    def test_admin_make_active_action(self):
        """Test action 'Activer les utilisateurs'."""
        url = reverse('admin:accounts_user_changelist')
        data = {
            'action': 'make_active',
            '_selected_action': [self.user2.id],
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.user2.refresh_from_db()
        self.assertTrue(self.user2.is_active)

    def test_admin_make_inactive_action(self):
        """Test action 'Désactiver les utilisateurs'."""
        url = reverse('admin:accounts_user_changelist')
        data = {
            'action': 'make_inactive',
            '_selected_action': [self.user1.id],
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.user1.refresh_from_db()
        self.assertFalse(self.user1.is_active)

    def test_admin_make_staff_action(self):
        """Test action 'Promouvoir en administrateur'."""
        url = reverse('admin:accounts_user_changelist')
        data = {
            'action': 'make_staff',
            '_selected_action': [self.user1.id],
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.user1.refresh_from_db()
        self.assertTrue(self.user1.is_staff)

    def test_admin_remove_staff_action(self):
        """Test action 'Rétrograder des administrateurs'."""
        self.user1.is_staff = True
        self.user1.save()
        url = reverse('admin:accounts_user_changelist')
        data = {
            'action': 'remove_staff',
            '_selected_action': [self.user1.id],
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.user1.refresh_from_db()
        self.assertFalse(self.user1.is_staff)

    def test_admin_export_as_csv(self):
        """Test export CSV des utilisateurs."""
        url = reverse('admin:accounts_user_changelist')
        data = {
            'action': 'export_as_csv',
            '_selected_action': [self.user1.id, self.user2.id],
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('Email', response.content.decode('utf-8'))
        self.assertIn('user1@example.com', response.content.decode('utf-8'))
        self.assertIn('user2@example.com', response.content.decode('utf-8'))

    def test_admin_search(self):
        """Test recherche dans l'admin."""
        url = reverse('admin:accounts_user_changelist')
        response = self.client.get(url, {'q': 'user1'})
        self.assertEqual(response.status_code, 200)

    def test_admin_filter(self):
        """Test filtres dans l'admin."""
        url = reverse('admin:accounts_user_changelist')
        response = self.client.get(url, {'is_active__exact': '1'})
        self.assertEqual(response.status_code, 200)

    def test_admin_permissions(self):
        """Test que seuls les admins peuvent accéder."""
        # Se déconnecter
        self.client.logout()

        # Utilisateur normal
        normal_user = User.objects.create_user(
            email='normal@example.com',
            password='testpass123',
            email_verified=True
        )
        self.client.force_login(normal_user)

        url = reverse('admin:accounts_user_changelist')
        response = self.client.get(url)
        # Doit rediriger vers la page de connexion admin
        self.assertEqual(response.status_code, 302)

