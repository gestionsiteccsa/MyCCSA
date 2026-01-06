"""
Tests pour les vues de l'application dashboard.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class DashboardViewTest(TestCase):
    """
    Tests pour la vue principale du dashboard.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123'
        )

    def test_dashboard_requires_superuser(self):
        """Test que seuls les superusers peuvent accéder."""
        # Utilisateur normal
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_superuser_access(self):
        """Test l'accès pour un superuser."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard administrateur')

    def test_dashboard_unauthenticated_redirect(self):
        """Test que les utilisateurs non authentifiés sont redirigés."""
        response = self.client.get(reverse('dashboard:index'))
        # Devrait rediriger vers la page de connexion
        self.assertEqual(response.status_code, 302)

    def test_dashboard_contains_stats(self):
        """Test que le dashboard affiche les statistiques."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('dashboard:index'))
        self.assertContains(response, 'Utilisateurs totaux')
        self.assertContains(response, 'Utilisateurs actifs')
        self.assertContains(response, 'Secteurs')

    def test_dashboard_contains_navigation(self):
        """Test que le dashboard contient la navigation."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('dashboard:index'))
        self.assertContains(response, 'Vue d\'ensemble')
        self.assertContains(response, 'Secteurs')
        self.assertContains(response, 'Utilisateurs')
        self.assertContains(response, 'Admin Django')

    def test_dashboard_contains_secteurs_links(self):
        """Test que le dashboard contient les liens vers les secteurs."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('dashboard:index'))
        # Vérifier que les URLs des secteurs sont présentes
        self.assertContains(response, reverse('secteurs:list'))
        self.assertContains(response, reverse('secteurs:create'))
        self.assertContains(response, reverse('secteurs:user_list'))


class DashboardUtilsTest(TestCase):
    """
    Tests pour les fonctions utilitaires du dashboard.
    """
    def setUp(self):
        """Configuration initiale."""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            is_active=True,
            email_verified=True
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            is_active=False
        )

    def test_get_dashboard_stats(self):
        """Test la fonction get_dashboard_stats."""
        from dashboard.utils import get_dashboard_stats

        stats = get_dashboard_stats()

        self.assertIn('total_users', stats)
        self.assertIn('active_users', stats)
        self.assertIn('verified_users', stats)
        self.assertIn('total_secteurs', stats)
        self.assertEqual(stats['total_users'], 2)
        self.assertEqual(stats['active_users'], 1)
        self.assertEqual(stats['verified_users'], 1)

    def test_get_dashboard_stats_with_secteurs(self):
        """Test les statistiques avec des secteurs."""
        try:
            from secteurs.models import Secteur
            from dashboard.utils import get_dashboard_stats

            secteur = Secteur.objects.create(
                nom='TEST',
                couleur='#ff0000',
                ordre=1
            )
            self.user1.secteurs.add(secteur)

            stats = get_dashboard_stats()
            self.assertGreaterEqual(stats['total_secteurs'], 1)
            self.assertGreaterEqual(stats['users_with_secteurs'], 1)
        except ImportError:
            # Si l'app secteurs n'est pas disponible, on skip ce test
            pass












