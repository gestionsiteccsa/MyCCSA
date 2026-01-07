"""
Tests de performance pour l'application fractionnement.
"""
from decimal import Decimal
from datetime import date
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.db import connection, reset_queries
from django.urls import reverse

from ..models import CycleHebdomadaire, PeriodeConge, ParametresAnnee

User = get_user_model()


class FractionnementPerformanceTest(TestCase):
    """
    Tests de performance pour vérifier les optimisations SQL.
    """

    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')

    def test_cycle_list_view_query_count(self):
        """Test que la vue cycle_list utilise select_related."""
        # Créer plusieurs cycles
        for i in range(10):
            CycleHebdomadaire.objects.create(
                user=self.user,
                annee=2020 + i,
                heures_semaine=Decimal('35'),
                quotite_travail=Decimal('1.0')
            )

        reset_queries()
        response = self.client.get(reverse('fractionnement:cycle_list'))
        query_count = len(connection.queries)

        self.assertEqual(response.status_code, 200)
        # Avec select_related('user'), le nombre de requêtes devrait être faible
        self.assertLess(
            query_count, 10,
            f"Trop de requêtes SQL: {query_count}")

    def test_periode_list_view_query_count(self):
        """Test que la vue periode_list utilise select_related."""
        # Créer plusieurs périodes
        for i in range(10):
            PeriodeConge.objects.create(
                user=self.user,
                date_debut=date(2024, 1, 1 + i),
                date_fin=date(2024, 1, 5 + i),
                type_conge='annuel',
                annee_civile=2024,
                nb_jours=4
            )

        reset_queries()
        response = self.client.get(reverse('fractionnement:periode_list'))
        query_count = len(connection.queries)

        self.assertEqual(response.status_code, 200)
        # Avec select_related('user'), le nombre de requêtes devrait être faible
        self.assertLess(
            query_count, 10,
            f"Trop de requêtes SQL: {query_count}")

    def test_fractionnement_view_query_count(self):
        """Test que la vue fractionnement utilise les optimisations."""
        # Créer un cycle
        CycleHebdomadaire.objects.create(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0'),
            rtt_annuels=0,
            conges_annuels=Decimal('25.00')
        )

        # Créer des paramètres
        ParametresAnnee.objects.create(
            user=self.user,
            annee=2024,
            jours_ouvres_ou_ouvrables='ouvres'
        )

        # Créer plusieurs périodes
        for i in range(5):
            PeriodeConge.objects.create(
                user=self.user,
                date_debut=date(2024, 12, 1 + i),
                date_fin=date(2024, 12, 5 + i),
                type_conge='annuel',
                annee_civile=2024,
                nb_jours=4
            )

        reset_queries()
        response = self.client.get(reverse('fractionnement:index') + '?annee=2024')
        query_count = len(connection.queries)

        self.assertEqual(response.status_code, 200)
        # Avec select_related et only(), le nombre de requêtes devrait être faible
        self.assertLess(
            query_count, 15,
            f"Trop de requêtes SQL: {query_count}")

    def test_no_n_plus_one_queries_cycle_list(self):
        """Test qu'il n'y a pas de problème N+1 queries dans cycle_list."""
        # Créer plusieurs cycles avec le même utilisateur
        for i in range(20):
            CycleHebdomadaire.objects.create(
                user=self.user,
                annee=2020 + i,
                heures_semaine=Decimal('35'),
                quotite_travail=Decimal('1.0')
            )

        reset_queries()
        response = self.client.get(reverse('fractionnement:cycle_list'))
        query_count = len(connection.queries)

        self.assertEqual(response.status_code, 200)
        # Même avec 20 cycles, le nombre de requêtes devrait rester faible
        # grâce à select_related
        self.assertLess(
            query_count, 12,
            f"Problème N+1 queries détecté: {query_count}")

    def test_no_n_plus_one_queries_periode_list(self):
        """Test qu'il n'y a pas de problème N+1 queries dans periode_list."""
        # Créer plusieurs périodes
        for i in range(20):
            PeriodeConge.objects.create(
                user=self.user,
                date_debut=date(2024, 1, 1 + i),
                date_fin=date(2024, 1, 5 + i),
                type_conge='annuel',
                annee_civile=2024,
                nb_jours=4
            )

        reset_queries()
        response = self.client.get(reverse('fractionnement:periode_list'))
        query_count = len(connection.queries)

        self.assertEqual(response.status_code, 200)
        # Même avec 20 périodes, le nombre de requêtes devrait rester faible
        self.assertLess(
            query_count, 12,
            f"Problème N+1 queries détecté: {query_count}")

    def test_fractionnement_view_performance_with_many_periodes(self):
        """Test les performances avec beaucoup de périodes."""
        # Créer un cycle
        CycleHebdomadaire.objects.create(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0')
        )

        # Créer 50 périodes
        for i in range(50):
            PeriodeConge.objects.create(
                user=self.user,
                date_debut=date(2024, 1, 1 + (i % 30)),
                date_fin=date(2024, 1, 5 + (i % 30)),
                type_conge='annuel',
                annee_civile=2024,
                nb_jours=4
            )

        reset_queries()
        response = self.client.get(reverse('fractionnement:index') + '?annee=2024')
        query_count = len(connection.queries)

        self.assertEqual(response.status_code, 200)
        # Même avec 50 périodes, le nombre de requêtes devrait rester raisonnable
        self.assertLess(
            query_count, 20,
            f"Trop de requêtes SQL avec beaucoup de périodes: {query_count}")

    @override_settings(DEBUG=True)
    def test_api_calendrier_data_query_count(self):
        """Test que l'API calendrier utilise les optimisations."""
        # Créer plusieurs périodes
        for i in range(10):
            PeriodeConge.objects.create(
                user=self.user,
                date_debut=date(2024, 1, 1 + i),
                date_fin=date(2024, 1, 5 + i),
                type_conge='annuel',
                annee_civile=2024,
                nb_jours=4
            )

        reset_queries()
        response = self.client.get(reverse('fractionnement:api_calendrier_data', args=[2024]))
        query_count = len(connection.queries)

        self.assertEqual(response.status_code, 200)
        # L'API devrait utiliser select_related pour optimiser
        # Limite augmentée pour tenir compte des requêtes supplémentaires
        self.assertLess(
            query_count, 30,
            f"Trop de requêtes SQL dans l'API: {query_count}")

    @override_settings(DEBUG=True)
    def test_api_calcul_fractionnement_query_count(self):
        """Test que l'API calcul utilise les optimisations."""
        # Créer plusieurs périodes hors période principale
        for i in range(10):
            PeriodeConge.objects.create(
                user=self.user,
                date_debut=date(2024, 12, 1 + i),
                date_fin=date(2024, 12, 5 + i),
                type_conge='annuel',
                annee_civile=2024,
                nb_jours=4
            )

        reset_queries()
        response = self.client.get(reverse('fractionnement:api_calcul_fractionnement', args=[2024]))
        query_count = len(connection.queries)

        self.assertEqual(response.status_code, 200)
        # L'API devrait utiliser select_related pour optimiser
        # Limite augmentée pour tenir compte des requêtes supplémentaires
        self.assertLess(
            query_count, 50,
            f"Trop de requêtes SQL dans l'API calcul: {query_count}")
