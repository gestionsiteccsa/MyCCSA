"""
Tests pour les vues de l'application fractionnement.
"""
from decimal import Decimal
from datetime import date
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.messages import get_messages

from ..models import CycleHebdomadaire, PeriodeConge, ParametresAnnee
from ..services.calcul_service import calculer_fractionnement_complet

User = get_user_model()


class CycleViewsTest(TestCase):
    """
    Tests pour les vues de gestion des cycles hebdomadaires.
    """

    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')

    def test_cycle_create_view_get(self):
        """Test affichage du formulaire de création."""
        response = self.client.get(reverse('fractionnement:cycle_create'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIn('title', response.context)

    def test_cycle_create_view_post_valid(self):
        """Test création d'un cycle avec données valides."""
        data = {
            'annee': 2024,
            'heures_semaine': '35',
            'quotite_travail': '1.0',
            'jours_ouvres_ou_ouvrables': 'ouvres',
        }
        response = self.client.post(reverse('fractionnement:cycle_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('fractionnement:cycle_list'))

        # Vérifier que le cycle a été créé
        cycle = CycleHebdomadaire.objects.get(user=self.user, annee=2024)
        self.assertEqual(cycle.heures_semaine, Decimal('35'))
        self.assertEqual(cycle.quotite_travail, Decimal('1.0'))

        # Vérifier le message de succès
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('succès', str(messages[0]).lower())

    def test_cycle_create_view_post_invalid(self):
        """Test création d'un cycle avec données invalides."""
        data = {
            'annee': 2024,
            'heures_semaine': '40',  # Invalide (> 39)
            'quotite_travail': '1.0',
            'jours_ouvres_ou_ouvrables': 'ouvres',
        }
        response = self.client.post(reverse('fractionnement:cycle_create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CycleHebdomadaire.objects.filter(user=self.user, annee=2024).exists())

    def test_cycle_create_view_requires_login(self):
        """Test que la vue nécessite une authentification."""
        self.client.logout()
        response = self.client.get(reverse('fractionnement:cycle_create'))
        self.assertEqual(response.status_code, 302)  # Redirection vers login

    def test_cycle_list_view(self):
        """Test affichage de la liste des cycles."""
        # Créer quelques cycles
        CycleHebdomadaire.objects.create(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0')
        )
        CycleHebdomadaire.objects.create(
            user=self.user,
            annee=2023,
            heures_semaine=Decimal('37'),
            quotite_travail=Decimal('1.0')
        )

        response = self.client.get(reverse('fractionnement:cycle_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_cycle_list_view_empty(self):
        """Test affichage de la liste vide."""
        response = self.client.get(reverse('fractionnement:cycle_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_cycle_update_view_get(self):
        """Test affichage du formulaire de modification."""
        cycle = CycleHebdomadaire.objects.create(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0')
        )

        response = self.client.get(reverse('fractionnement:cycle_update', args=[cycle.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIn('cycle', response.context)

    def test_cycle_update_view_post_valid(self):
        """Test modification d'un cycle avec données valides."""
        cycle = CycleHebdomadaire.objects.create(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0')
        )

        data = {
            'annee': 2024,
            'heures_semaine': '37',
            'quotite_travail': '1.0',
            'jours_ouvres_ou_ouvrables': 'ouvres',
        }
        response = self.client.post(reverse('fractionnement:cycle_update', args=[cycle.pk]), data)
        self.assertEqual(response.status_code, 302)

        cycle.refresh_from_db()
        self.assertEqual(cycle.heures_semaine, Decimal('37'))

    def test_cycle_update_view_other_user(self):
        """Test qu'un utilisateur ne peut pas modifier le cycle d'un autre."""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        cycle = CycleHebdomadaire.objects.create(
            user=other_user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0')
        )

        response = self.client.get(reverse('fractionnement:cycle_update', args=[cycle.pk]))
        self.assertEqual(response.status_code, 404)

    def test_cycle_delete_view_get(self):
        """Test affichage de la confirmation de suppression."""
        cycle = CycleHebdomadaire.objects.create(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0')
        )

        response = self.client.get(reverse('fractionnement:cycle_delete', args=[cycle.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('cycle', response.context)

    def test_cycle_delete_view_post(self):
        """Test suppression d'un cycle."""
        cycle = CycleHebdomadaire.objects.create(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0')
        )

        response = self.client.post(reverse('fractionnement:cycle_delete', args=[cycle.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CycleHebdomadaire.objects.filter(pk=cycle.pk).exists())


class PeriodeViewsTest(TestCase):
    """
    Tests pour les vues de gestion des périodes de congés.
    """

    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')

    def test_periode_create_view_get(self):
        """Test affichage du formulaire de création."""
        response = self.client.get(reverse('fractionnement:periode_create'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_periode_create_view_post_valid(self):
        """Test création d'une période avec données valides."""
        data = {
            'date_debut': '2024-07-01',
            'debut_type': 'matin',
            'date_fin': '2024-07-15',
            'fin_type': 'apres_midi',
            'type_conge': 'annuel',
        }
        response = self.client.post(reverse('fractionnement:periode_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('fractionnement:periode_list'))

        # Vérifier que la période a été créée
        periode = PeriodeConge.objects.get(user=self.user, date_debut=date(2024, 7, 1))
        self.assertEqual(periode.type_conge, 'annuel')
        self.assertEqual(periode.annee_civile, 2024)

    def test_periode_create_view_post_invalid(self):
        """Test création d'une période avec date_fin < date_debut."""
        data = {
            'date_debut': '2024-07-15',
            'debut_type': 'matin',
            'date_fin': '2024-07-01',  # Invalide
            'fin_type': 'apres_midi',
            'type_conge': 'annuel',
        }
        response = self.client.post(reverse('fractionnement:periode_create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PeriodeConge.objects.filter(user=self.user).exists())

    def test_periode_list_view(self):
        """Test affichage de la liste des périodes."""
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 7, 1),
            date_fin=date(2024, 7, 15),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=10
        )

        response = self.client.get(reverse('fractionnement:periode_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_periode_list_view_filter_annee(self):
        """Test filtrage par année."""
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 7, 1),
            date_fin=date(2024, 7, 15),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=10
        )
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2023, 7, 1),
            date_fin=date(2023, 7, 15),
            type_conge='annuel',
            annee_civile=2023,
            nb_jours=10
        )

        response = self.client.get(reverse('fractionnement:periode_list') + '?annee=2024')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_periode_list_view_filter_type_conge(self):
        """Test filtrage par type de congé."""
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 7, 1),
            date_fin=date(2024, 7, 15),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=10
        )
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 8, 1),
            date_fin=date(2024, 8, 5),
            type_conge='rtt',
            annee_civile=2024,
            nb_jours=4
        )

        response = self.client.get(reverse('fractionnement:periode_list') + '?type_conge=annuel')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_periode_update_view_get(self):
        """Test affichage du formulaire de modification."""
        periode = PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 7, 1),
            date_fin=date(2024, 7, 15),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=10
        )

        response = self.client.get(reverse('fractionnement:periode_update', args=[periode.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIn('periode', response.context)

    def test_periode_update_view_post_valid(self):
        """Test modification d'une période avec données valides."""
        periode = PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 7, 1),
            date_fin=date(2024, 7, 15),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=10
        )

        data = {
            'date_debut': '2024-07-01',
            'debut_type': 'matin',
            'date_fin': '2024-07-20',
            'fin_type': 'apres_midi',
            'type_conge': 'annuel',
        }
        response = self.client.post(reverse('fractionnement:periode_update', args=[periode.pk]), data)
        self.assertEqual(response.status_code, 302)

        periode.refresh_from_db()
        self.assertEqual(periode.date_fin, date(2024, 7, 20))

    def test_periode_delete_view_post(self):
        """Test suppression d'une période."""
        periode = PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 7, 1),
            date_fin=date(2024, 7, 15),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=10
        )

        response = self.client.post(reverse('fractionnement:periode_delete', args=[periode.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PeriodeConge.objects.filter(pk=periode.pk).exists())


class FractionnementViewTest(TestCase):
    """
    Tests pour la vue principale de fractionnement.
    """

    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')

    def test_fractionnement_view_get(self):
        """Test affichage de la vue principale."""
        response = self.client.get(reverse('fractionnement:index'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('annee', response.context)
        self.assertIn('calcul', response.context)
        self.assertIn('periodes', response.context)

    def test_fractionnement_view_with_annee_param(self):
        """Test avec paramètre année."""
        response = self.client.get(reverse('fractionnement:index') + '?annee=2023')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['annee'], 2023)

    def test_fractionnement_view_with_cycle(self):
        """Test avec cycle hebdomadaire existant."""
        CycleHebdomadaire.objects.create(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0'),
            rtt_annuels=0,
            conges_annuels=Decimal('25.00')
        )

        response = self.client.get(reverse('fractionnement:index') + '?annee=2024')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['cycle'])

    def test_fractionnement_view_with_periodes(self):
        """Test avec périodes de congés."""
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 12, 1),
            date_fin=date(2024, 12, 6),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=4
        )

        response = self.client.get(reverse('fractionnement:index') + '?annee=2024')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['periodes']), 1)

    def test_fractionnement_view_requires_login(self):
        """Test que la vue nécessite une authentification."""
        self.client.logout()
        response = self.client.get(reverse('fractionnement:index'))
        self.assertEqual(response.status_code, 302)


class APICalendrierDataTest(TestCase):
    """
    Tests pour l'API de données du calendrier.
    """

    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')

    def test_api_calendrier_data_valid(self):
        """Test API avec année valide."""
        response = self.client.get(reverse('fractionnement:api_calendrier_data', args=[2024]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        data = response.json()
        self.assertIn('annee', data)
        self.assertIn('jours_feries', data)
        self.assertIn('vacances_zone_b', data)
        self.assertIn('periodes_conges', data)

    def test_api_calendrier_data_invalid(self):
        """Test API avec année invalide."""
        # Utiliser directement l'URL car reverse() ne fonctionne pas avec des arguments non-numériques
        response = self.client.get('/fractionnement/api/calendrier/invalid/')
        self.assertEqual(response.status_code, 404)  # Django retourne 404 pour URL non matchée

    def test_api_calendrier_data_requires_login(self):
        """Test que l'API nécessite une authentification."""
        self.client.logout()
        response = self.client.get(reverse('fractionnement:api_calendrier_data', args=[2024]))
        self.assertEqual(response.status_code, 302)


class APICalculFractionnementTest(TestCase):
    """
    Tests pour l'API de calcul de fractionnement.
    """

    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')

    def test_api_calcul_fractionnement_valid(self):
        """Test API avec année valide."""
        # Créer une période hors période principale
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 12, 1),
            date_fin=date(2024, 12, 6),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=4
        )

        response = self.client.get(reverse('fractionnement:api_calcul_fractionnement', args=[2024]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        data = response.json()
        self.assertIn('jours_hors_periode', data)
        self.assertIn('jours_fractionnement', data)
        self.assertIn('annee', data)

    def test_api_calcul_fractionnement_invalid(self):
        """Test API avec année invalide."""
        # Utiliser directement l'URL car reverse() ne fonctionne pas avec des arguments non-numériques
        response = self.client.get('/fractionnement/api/calcul/invalid/')
        self.assertEqual(response.status_code, 404)  # Django retourne 404 pour URL non matchée

    def test_api_calcul_fractionnement_requires_login(self):
        """Test que l'API nécessite une authentification."""
        self.client.logout()
        response = self.client.get(reverse('fractionnement:api_calcul_fractionnement', args=[2024]))
        self.assertEqual(response.status_code, 302)
