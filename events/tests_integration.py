"""
Tests d'intégration pour l'application events.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from role.models import Role
from .models import Event
from secteurs.models import Secteur

User = get_user_model()


class EventWorkflowDGADGSTest(TestCase):
    """
    Tests d'intégration pour le workflow de validation DGA/DGS.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client()

        # Créer les rôles (avec niveau requis) - utiliser get_or_create pour éviter les conflits
        # Utiliser des niveaux uniques (10, 11, 12) pour éviter les conflits avec les migrations
        self.role_dga, _ = Role.objects.get_or_create(nom='DGA_TEST', defaults={'niveau': 10})
        self.role_dgs, _ = Role.objects.get_or_create(nom='DGS_TEST', defaults={'niveau': 11})
        self.role_communication, _ = Role.objects.get_or_create(
            nom='Chargé de communication', defaults={'niveau': 12}
        )

        # Créer les utilisateurs
        self.user_creator = User.objects.create_user(
            email='creator@example.com',
            password='testpass123',
            email_verified=True
        )
        # Donner les permissions pour créer des événements
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(Event)
        permission = Permission.objects.get(
            codename='add_event',
            content_type=content_type
        )
        self.user_creator.user_permissions.add(permission)

        self.user_dga = User.objects.create_user(
            email='dga@example.com',
            password='testpass123',
            email_verified=True,
            role=self.role_dga
        )

        self.user_dgs = User.objects.create_user(
            email='dgs@example.com',
            password='testpass123',
            email_verified=True,
            role=self.role_dgs
        )

        self.user_communication = User.objects.create_user(
            email='communication@example.com',
            password='testpass123',
            email_verified=True,
            role=self.role_communication
        )

        # Créer un secteur
        self.secteur = Secteur.objects.create(
            nom='SANTÉ_INTEGRATION',
            couleur='#b4c7e7',
            ordre=1
        )

    def test_complete_validation_workflow_dga(self):
        """
        Test le workflow complet de validation DGA.

        Scénario :
        1. Créateur crée un événement avec demande de validation DGA
        2. DGA valide l'événement
        3. Vérifier que le statut est mis à jour
        """
        # Étape 1 : Créateur crée un événement avec demande de validation DGA
        self.client.force_login(self.user_creator)
        data = {
            'titre': 'Événement à valider DGA',
            'description': 'Description de test',
            'date_debut': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'timezone': 'Europe/Paris',
            'adresse_ville': 'Paris',
            'demande_validation_dga': True,
            'secteurs': [self.secteur.id]
        }
        response = self.client.post(reverse('events:create'), data)
        self.assertEqual(response.status_code, 302)

        # Récupérer l'événement créé
        event = Event.objects.get(titre='Événement à valider DGA')
        self.assertEqual(event.statut_validation_dga, 'en_attente')
        self.assertTrue(event.demande_validation_dga)

        # Étape 2 : DGA valide l'événement
        self.client.force_login(self.user_dga)
        validation_data = {
            'action': 'valider',
            'validation_type': 'dga',
            'commentaire': 'Validation DGA approuvée'
        }
        response = self.client.post(
            reverse('events:validate', kwargs={'pk': event.pk}),
            validation_data
        )
        self.assertEqual(response.status_code, 302)

        # Étape 3 : Vérifier que le statut est mis à jour
        event.refresh_from_db()
        self.assertEqual(event.statut_validation_dga, 'valide')
        self.assertEqual(event.validateur_dga, self.user_dga)
        self.assertIsNotNone(event.date_validation_dga)
        self.assertEqual(event.commentaire_validation_dga, 'Validation DGA approuvée')

    def test_complete_validation_workflow_dgs(self):
        """
        Test le workflow complet de validation DGS.

        Scénario :
        1. Créateur crée un événement avec demande de validation DGS
        2. DGS valide l'événement
        3. Vérifier que le statut est mis à jour
        """
        # Étape 1 : Créateur crée un événement avec demande de validation DGS
        self.client.force_login(self.user_creator)
        data = {
            'titre': 'Événement à valider DGS',
            'description': 'Description de test',
            'date_debut': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'timezone': 'Europe/Paris',
            'adresse_ville': 'Paris',
            'demande_validation_dgs': True,
            'secteurs': [self.secteur.id]
        }
        response = self.client.post(reverse('events:create'), data)
        self.assertEqual(response.status_code, 302)

        # Récupérer l'événement créé
        event = Event.objects.get(titre='Événement à valider DGS')
        self.assertEqual(event.statut_validation_dgs, 'en_attente')
        self.assertTrue(event.demande_validation_dgs)

        # Étape 2 : DGS valide l'événement
        self.client.force_login(self.user_dgs)
        validation_data = {
            'action': 'valider',
            'validation_type': 'dgs',
            'commentaire': 'Validation DGS approuvée'
        }
        response = self.client.post(
            reverse('events:validate', kwargs={'pk': event.pk}),
            validation_data
        )
        self.assertEqual(response.status_code, 302)

        # Étape 3 : Vérifier que le statut est mis à jour
        event.refresh_from_db()
        self.assertEqual(event.statut_validation_dgs, 'valide')
        self.assertEqual(event.validateur_dgs, self.user_dgs)
        self.assertIsNotNone(event.date_validation_dgs)
        self.assertEqual(event.commentaire_validation_dgs, 'Validation DGS approuvée')

    def test_validation_refusal_workflow(self):
        """
        Test le workflow de refus de validation.

        Scénario :
        1. Créateur crée un événement avec demande de validation DGA
        2. DGA refuse l'événement
        3. Vérifier que le statut global est 'refuse'
        """
        # Étape 1 : Créateur crée un événement
        self.client.force_login(self.user_creator)
        data = {
            'titre': 'Événement refusé',
            'date_debut': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'timezone': 'Europe/Paris',
            'adresse_ville': 'Paris',
            'demande_validation_dga': True,
        }
        response = self.client.post(reverse('events:create'), data)
        self.assertEqual(response.status_code, 302)

        event = Event.objects.get(titre='Événement refusé')

        # Étape 2 : DGA refuse l'événement
        self.client.force_login(self.user_dga)
        validation_data = {
            'action': 'refuser',
            'validation_type': 'dga',
            'commentaire': 'Événement refusé pour raison X'
        }
        response = self.client.post(
            reverse('events:validate', kwargs={'pk': event.pk}),
            validation_data
        )
        self.assertEqual(response.status_code, 302)

        # Étape 3 : Vérifier que le statut global est 'refuse'
        event.refresh_from_db()
        self.assertEqual(event.statut_validation_dga, 'refuse')
        self.assertEqual(event.statut_global_validation, 'refuse')

    def test_stats_view_permissions(self):
        """
        Test que seuls les utilisateurs autorisés peuvent voir les statistiques.
        """
        # Test avec utilisateur communication (autorisé)
        self.client.force_login(self.user_communication)
        response = self.client.get(reverse('events:stats'))
        self.assertEqual(response.status_code, 200)

        # Test avec créateur (non autorisé)
        self.client.force_login(self.user_creator)
        response = self.client.get(reverse('events:stats'))
        # Devrait rediriger ou retourner 403
        self.assertIn(response.status_code, [302, 403])

    def test_validation_permissions_dga_only(self):
        """
        Test que seul le DGA peut valider les événements demandant validation DGA.
        """
        # Créer un événement avec demande de validation DGA
        self.client.force_login(self.user_creator)
        data = {
            'titre': 'Événement DGA',
            'date_debut': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'timezone': 'Europe/Paris',
            'adresse_ville': 'Paris',
            'demande_validation_dga': True,
        }
        self.client.post(reverse('events:create'), data)
        event = Event.objects.get(titre='Événement DGA')

        # Tenter de valider avec DGS (ne devrait pas pouvoir)
        self.client.force_login(self.user_dgs)
        validation_data = {
            'action': 'valider',
            'validation_type': 'dga',  # DGS essaie de valider DGA
        }
        response = self.client.post(
            reverse('events:validate', kwargs={'pk': event.pk}),
            validation_data
        )
        # Devrait rediriger avec un message d'erreur
        self.assertEqual(response.status_code, 302)

        # Vérifier que le statut n'a pas changé
        event.refresh_from_db()
        self.assertEqual(event.statut_validation_dga, 'en_attente')

    def test_my_events_view_shows_validation_requests(self):
        """
        Test que la vue 'mes événements' affiche les événements avec demande de validation
        même s'ils sont passés.
        """
        # Créer un événement passé avec demande de validation
        self.client.force_login(self.user_creator)
        past_date = timezone.now() - timezone.timedelta(days=1)
        event = Event.objects.create(
            titre='Événement passé avec validation',
            date_debut=past_date,
            createur=self.user_creator,
            demande_validation_dga=True,
            statut_validation_dga='en_attente'
        )

        # Accéder à la vue mes événements
        response = self.client.get(reverse('events:my_events'))
        self.assertEqual(response.status_code, 200)

        # Vérifier que l'événement est dans la liste
        events_in_context = response.context['events']
        self.assertIn(event, events_in_context)
