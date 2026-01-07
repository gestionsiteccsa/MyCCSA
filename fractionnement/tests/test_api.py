"""
Tests pour les endpoints API de l'application fractionnement.
"""
from datetime import date
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from ..models import CycleHebdomadaire, PeriodeConge

User = get_user_model()


class FractionnementAPITest(TestCase):
    """
    Tests pour les vues API JSON.
    """

    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='api_test@example.com',
            password='testpass123',
            email_verified=True
        )
        self.client.login(email='api_test@example.com', password='testpass123')

        # Créer des données de test
        self.annee = 2024
        CycleHebdomadaire.objects.create(
            user=self.user,
            annee=self.annee,
            heures_semaine=35,
            quotite_travail=1.0
        )

    def test_api_calendrier_data_success(self):
        """Test que l'API calendrier retourne des données valides."""
        # Ajouter une période de congé
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 7, 1),
            date_fin=date(2024, 7, 5),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=5
        )

        url = reverse('fractionnement:api_calendrier_data', args=[self.annee])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['annee'], self.annee)
        self.assertTrue(len(data['periodes_conges']) > 0)
        self.assertEqual(data['periodes_conges'][0]['type_conge'], 'annuel')

    def test_api_calendrier_data_invalid_year(self):
        """Test l'API calendrier avec une année invalide (non-entière)."""
        # On utilise l'URL en dur car reverse échouera avec 'abc'
        response = self.client.get('/fractionnement/api/calendrier/abc/')
        # Django retournera une 404 car l'URL ne matche pas le pattern <int:annee>
        self.assertEqual(response.status_code, 404)

    def test_api_calcul_fractionnement_success(self):
        """Test que l'API calcul retourne des données valides."""
        url = reverse('fractionnement:api_calcul_fractionnement', args=[self.annee])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('jours_hors_periode', data)
        self.assertIn('jours_fractionnement', data)

    def test_api_calcul_fractionnement_unauthenticated(self):
        """Test que l'API requiert l'authentification."""
        self.client.logout()
        url = reverse('fractionnement:api_calcul_fractionnement', args=[self.annee])
        response = self.client.get(url)
        # Redirection vers login
        self.assertEqual(response.status_code, 302)

    def test_api_calcul_fractionnement_error_handling(self):
        """Test la gestion d'erreur dans l'API calcul."""
        # Supprimer le cycle pour provoquer une erreur potentielle si le service n'est pas robuste
        # (Dans ce cas, le service devrait retourner 0 ou une erreur gérée)
        CycleHebdomadaire.objects.all().delete()
        url = reverse('fractionnement:api_calcul_fractionnement', args=[self.annee])
        response = self.client.get(url)

        # Le service actuel semble gérer l'absence de cycle en retournant 0 ou une erreur 400
        self.assertIn(response.status_code, [200, 400])
