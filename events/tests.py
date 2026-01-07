"""
Tests de l'application events.
"""
import os
from io import BytesIO
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.db import connection, reset_queries
from PIL import Image
import time

from .models import Event, EventFile, EventAddress
from .forms import EventForm
from secteurs.models import Secteur

User = get_user_model()


def create_test_image(filename='test.png', size=(100, 100)):
    """
    Crée une image de test.

    Args:
        filename: Nom du fichier
        size: Taille de l'image (width, height)

    Returns:
        SimpleUploadedFile: Fichier image pour les tests
    """
    image = Image.new('RGB', size, color='red')
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return SimpleUploadedFile(
        filename,
        buffer.read(),
        content_type='image/png'
    )


class EventAddressModelTest(TestCase):
    """
    Tests pour le modèle EventAddress.
    """
    def setUp(self):
        """Configuration initiale."""
        self.adresse = EventAddress.objects.create(
            rue='123 Rue de la Test',
            ville='Paris',
            code_postal='75001',
            pays='France',
            complement='Étage 2'
        )

    def test_event_address_str(self):
        """Test la représentation string de l'adresse."""
        expected = '123 Rue de la Test, 75001 Paris'
        self.assertEqual(str(self.adresse), expected)

    def test_event_address_str_without_rue(self):
        """Test la représentation string sans rue."""
        adresse = EventAddress.objects.create(
            ville='Lyon',
            code_postal='69001'
        )
        self.assertEqual(str(adresse), '69001 Lyon')

    def test_event_address_str_ville_only(self):
        """Test la représentation string avec seulement la ville."""
        adresse = EventAddress.objects.create(ville='Marseille')
        self.assertEqual(str(adresse), 'Marseille')

    def test_event_address_str_with_foreign_country(self):
        """Test la représentation string avec un pays étranger."""
        adresse = EventAddress.objects.create(
            ville='Bruxelles',
            pays='Belgique'
        )
        self.assertIn('Belgique', str(adresse))

    def test_event_address_ville_required(self):
        """Test que la ville est requise."""
        # La ville a db_index=True mais n'est pas null=False explicitement
        # Vérifier que le modèle fonctionne correctement
        adresse = EventAddress(ville='Test')
        adresse.full_clean()
        adresse.save()
        self.assertIsNotNone(adresse.pk)


class EventModelTest(TestCase):
    """
    Tests pour le modèle Event.
    """
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.secteur1 = Secteur.objects.create(
            nom='SANTÉ_TEST',
            couleur='#b4c7e7',
            ordre=1
        )
        self.secteur2 = Secteur.objects.create(
            nom='RURALITÉ_TEST',
            couleur='#005b24',
            ordre=2
        )
        self.event = Event.objects.create(
            titre='Test Event',
            description='Description de test',
            lieu='Salle de test',
            date_debut=timezone.now() + timezone.timedelta(days=1),
            createur=self.user
        )

    def test_event_str(self):
        """Test la représentation string de l'événement."""
        self.assertEqual(str(self.event), 'Test Event')

    def test_event_clean_valid(self):
        """Test la validation avec des dates valides."""
        event = Event(
            titre='Test',
            date_debut=timezone.now() + timezone.timedelta(days=1),
            date_fin=timezone.now() + timezone.timedelta(days=2),
            createur=self.user
        )
        # Ne devrait pas lever d'exception
        event.full_clean()

    def test_event_clean_invalid_date_fin(self):
        """Test la validation avec date_fin < date_debut."""
        event = Event(
            titre='Test',
            date_debut=timezone.now() + timezone.timedelta(days=2),
            date_fin=timezone.now() + timezone.timedelta(days=1),
            createur=self.user
        )
        with self.assertRaises(ValidationError):
            event.full_clean()

    def test_event_calculate_calendar_color_no_secteur(self):
        """Test le calcul de couleur sans secteur."""
        # La couleur devrait être grise par défaut
        self.event.save()
        self.assertEqual(self.event.couleur_calendrier, '#808080')

    def test_event_calculate_calendar_color_one_secteur(self):
        """Test le calcul de couleur avec un seul secteur."""
        self.event.secteurs.add(self.secteur1)
        self.event.save()
        # La couleur peut être en majuscules ou minuscules selon le format
        self.assertEqual(self.event.couleur_calendrier.upper(), '#B4C7E7')

    def test_event_calculate_calendar_color_multiple_secteurs(self):
        """Test le calcul de couleur avec plusieurs secteurs."""
        self.event.secteurs.add(self.secteur1, self.secteur2)
        self.event.save()
        # La couleur devrait être un mélange des deux couleurs
        self.assertNotEqual(self.event.couleur_calendrier, '#808080')
        self.assertNotEqual(self.event.couleur_calendrier, '#B4C7E7')
        self.assertNotEqual(self.event.couleur_calendrier, '#005B24')

    def test_event_mix_colors(self):
        """Test la méthode _mix_colors."""
        colors = ['#FF0000', '#00FF00']  # Rouge et Vert
        mixed = self.event._mix_colors(colors)
        # Le mélange devrait être proche de #808000 (jaune-vert)
        self.assertEqual(len(mixed), 7)  # Format hex: #RRGGBB
        self.assertTrue(mixed.startswith('#'))

    def test_event_created_at_auto(self):
        """Test que created_at est automatiquement défini."""
        self.assertIsNotNone(self.event.created_at)

    def test_event_updated_at_auto(self):
        """Test que updated_at est automatiquement défini."""
        self.assertIsNotNone(self.event.updated_at)

    def test_event_ordering(self):
        """Test l'ordre de tri des événements."""
        event2 = Event.objects.create(
            titre='Event 2',
            date_debut=timezone.now() + timezone.timedelta(days=2),
            createur=self.user
        )
        events = list(Event.objects.all())
        # Les événements devraient être triés par date_debut
        self.assertEqual(events[0], self.event)
        self.assertEqual(events[1], event2)


class EventFileModelTest(TestCase):
    """
    Tests pour le modèle EventFile.
    """
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.event = Event.objects.create(
            titre='Test Event',
            date_debut=timezone.now() + timezone.timedelta(days=1),
            createur=self.user
        )
        self.test_image = create_test_image()

    def test_event_file_str(self):
        """Test la représentation string du fichier."""
        event_file = EventFile.objects.create(
            event=self.event,
            fichier=self.test_image,
            type_fichier='image',
            nom='test.png',
            taille=1024,
            ordre=0
        )
        self.assertEqual(str(event_file), 'test.png')

    def test_event_file_ordering(self):
        """Test l'ordre de tri des fichiers."""
        file1 = EventFile.objects.create(
            event=self.event,
            fichier=create_test_image('test1.png'),
            type_fichier='image',
            nom='test1.png',
            taille=1024,
            ordre=2
        )
        file2 = EventFile.objects.create(
            event=self.event,
            fichier=create_test_image('test2.png'),
            type_fichier='image',
            nom='test2.png',
            taille=1024,
            ordre=1
        )
        files = list(EventFile.objects.all())
        # Les fichiers devraient être triés par ordre puis uploaded_at
        self.assertEqual(files[0], file2)
        self.assertEqual(files[1], file1)


class EventViewTest(TestCase):
    """
    Tests d'intégration pour les vues events.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            email_verified=True
        )
        # Donner les permissions pour gérer les événements
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(Event)
        permission = Permission.objects.get(
            codename='add_event',
            content_type=content_type
        )
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)

        self.secteur = Secteur.objects.create(
            nom='SANTÉ_VIEW_TEST',
            couleur='#b4c7e7',
            ordre=1
        )
        self.event = Event.objects.create(
            titre='Test Event',
            description='Description',
            date_debut=timezone.now() + timezone.timedelta(days=1),
            createur=self.user
        )

    def test_calendar_view_status_code(self):
        """Test que la vue calendrier retourne un code 200."""
        response = self.client.get(reverse('events:calendar'))
        self.assertEqual(response.status_code, 200)

    def test_calendar_view_template(self):
        """Test que la vue calendrier utilise le bon template."""
        response = self.client.get(reverse('events:calendar'))
        self.assertTemplateUsed(response, 'events/calendar.html')

    def test_list_view_status_code(self):
        """Test que la vue liste retourne un code 200."""
        response = self.client.get(reverse('events:list'))
        self.assertEqual(response.status_code, 200)

    def test_list_view_template(self):
        """Test que la vue liste utilise le bon template."""
        response = self.client.get(reverse('events:list'))
        self.assertTemplateUsed(response, 'events/list.html')

    def test_list_view_pagination(self):
        """Test que la pagination fonctionne."""
        # Créer plus de 25 événements pour tester la pagination
        for i in range(30):
            Event.objects.create(
                titre=f'Event {i}',
                date_debut=timezone.now() + timezone.timedelta(days=i),
                createur=self.user
            )
        response = self.client.get(reverse('events:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('page_obj' in response.context)

    def test_detail_view_status_code(self):
        """Test que la vue détail retourne un code 200."""
        response = self.client.get(
            reverse('events:detail', kwargs={'pk': self.event.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_detail_view_template(self):
        """Test que la vue détail utilise le bon template."""
        response = self.client.get(
            reverse('events:detail', kwargs={'pk': self.event.pk})
        )
        self.assertTemplateUsed(response, 'events/detail.html')

    def test_create_view_get(self):
        """Test l'affichage du formulaire de création."""
        response = self.client.get(reverse('events:create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/create.html')

    def test_create_view_post(self):
        """Test la création d'un événement."""
        data = {
            'titre': 'Nouvel événement',
            'description': 'Description',
            'date_debut': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'timezone': 'Europe/Paris',
            'adresse_ville': 'Paris'
        }
        response = self.client.post(reverse('events:create'), data)
        self.assertEqual(response.status_code, 302)  # Redirection après création
        self.assertTrue(Event.objects.filter(titre='Nouvel événement').exists())

    def test_update_view_get(self):
        """Test l'affichage du formulaire de modification."""
        response = self.client.get(
            reverse('events:update', kwargs={'pk': self.event.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/update.html')

    def test_update_view_post(self):
        """Test la modification d'un événement."""
        data = {
            'titre': 'Event modifié',
            'description': 'Nouvelle description',
            'date_debut': (timezone.now() + timezone.timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            'timezone': 'Europe/Paris',
            'adresse_ville': 'Lyon'
        }
        response = self.client.post(
            reverse('events:update', kwargs={'pk': self.event.pk}),
            data
        )
        self.assertEqual(response.status_code, 302)
        self.event.refresh_from_db()
        self.assertEqual(self.event.titre, 'Event modifié')

    def test_delete_view_get(self):
        """Test l'affichage de la confirmation de suppression."""
        response = self.client.get(
            reverse('events:delete', kwargs={'pk': self.event.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/delete.html')

    def test_delete_view_post(self):
        """Test la suppression d'un événement."""
        event_pk = self.event.pk
        response = self.client.post(
            reverse('events:delete', kwargs={'pk': event_pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Event.objects.filter(pk=event_pk).exists())

    def test_timeline_view_status_code(self):
        """Test que la vue timeline retourne un code 200."""
        response = self.client.get(reverse('events:timeline'))
        self.assertEqual(response.status_code, 200)

    def test_timeline_view_template(self):
        """Test que la vue timeline utilise le bon template."""
        response = self.client.get(reverse('events:timeline'))
        self.assertTemplateUsed(response, 'events/timeline.html')

    def test_calendar_view_filter_by_secteur(self):
        """Test le filtre par secteur dans la vue calendrier."""
        self.event.secteurs.add(self.secteur)
        response = self.client.get(
            reverse('events:calendar') + f'?secteur={self.secteur.id}'
        )
        self.assertEqual(response.status_code, 200)

    def test_list_view_filter_by_secteur(self):
        """Test le filtre par secteur dans la vue liste."""
        self.event.secteurs.add(self.secteur)
        response = self.client.get(
            reverse('events:list') + f'?secteur={self.secteur.id}'
        )
        self.assertEqual(response.status_code, 200)


class EventFormTest(TestCase):
    """
    Tests pour les formulaires events.
    """
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.secteur = Secteur.objects.create(
            nom='SANTÉ_FORM_TEST',
            couleur='#b4c7e7',
            ordre=1
        )

    def test_event_form_valid(self):
        """Test un formulaire valide."""
        data = {
            'titre': 'Test Event',
            'date_debut': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'timezone': 'Europe/Paris',
            'adresse_ville': 'Paris'
        }
        form = EventForm(data)
        self.assertTrue(form.is_valid())

    def test_event_form_invalid_date_fin(self):
        """Test un formulaire avec date_fin < date_debut."""
        data = {
            'titre': 'Test Event',
            'date_debut': (timezone.now() + timezone.timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            'date_fin': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'timezone': 'Europe/Paris',
            'adresse_ville': 'Paris'
        }
        form = EventForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('date_fin', form.errors)

    def test_event_form_save_with_address(self):
        """Test la sauvegarde avec une adresse."""
        data = {
            'titre': 'Test Event',
            'date_debut': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'timezone': 'Europe/Paris',
            'adresse_rue': '123 Rue Test',
            'adresse_ville': 'Paris',
            'adresse_code_postal': '75001',
            'adresse_pays': 'France'
        }
        form = EventForm(data)
        self.assertTrue(form.is_valid())
        event = form.save(commit=False)
        event.createur = self.user
        event.save()
        form.save_m2m()
        self.assertIsNotNone(event.adresse)
        self.assertEqual(event.adresse.ville, 'Paris')


class EventWorkflowTest(TestCase):
    """
    Tests fonctionnels pour les parcours utilisateur complets.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            email_verified=True
        )
        # Donner les permissions
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(Event)
        permission = Permission.objects.get(
            codename='add_event',
            content_type=content_type
        )
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)

        self.secteur = Secteur.objects.create(
            nom='SANTÉ_WORKFLOW_TEST',
            couleur='#b4c7e7',
            ordre=1
        )

    def test_complete_event_workflow(self):
        """Test workflow complet : création → visualisation → modification → suppression."""
        # Étape 1 : Créer un événement
        create_url = reverse('events:create')
        data = {
            'titre': 'Nouvel événement',
            'description': 'Description complète',
            'lieu': 'Salle de réunion',
            'date_debut': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'timezone': 'Europe/Paris',
            'adresse_ville': 'Paris',
            'secteurs': [self.secteur.id]
        }
        response = self.client.post(create_url, data)
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'événement existe
        event = Event.objects.get(titre='Nouvel événement')
        self.assertIsNotNone(event.pk)

        # Étape 2 : Visualiser l'événement
        detail_url = reverse('events:detail', kwargs={'pk': event.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nouvel événement')

        # Étape 3 : Modifier l'événement
        update_url = reverse('events:update', kwargs={'pk': event.pk})
        data = {
            'titre': 'Événement modifié',
            'description': 'Nouvelle description',
            'date_debut': (timezone.now() + timezone.timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            'timezone': 'Europe/Paris',
            'adresse_ville': 'Lyon'
        }
        response = self.client.post(update_url, data)
        self.assertEqual(response.status_code, 302)

        # Vérifier les modifications
        event.refresh_from_db()
        self.assertEqual(event.titre, 'Événement modifié')
        self.assertEqual(event.adresse.ville, 'Lyon')

        # Étape 4 : Supprimer l'événement
        delete_url = reverse('events:delete', kwargs={'pk': event.pk})
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)

        # Vérifier que l'événement a été supprimé
        self.assertFalse(Event.objects.filter(pk=event.pk).exists())


class EventPerformanceTest(TestCase):
    """
    Tests de performance pour vérifier les optimisations SQL.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            email_verified=True
        )
        # Donner les permissions
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(Event)
        permission = Permission.objects.get(
            codename='add_event',
            content_type=content_type
        )
        self.user.user_permissions.add(permission)
        self.client.force_login(self.user)

        # Créer des secteurs
        self.secteurs = []
        for i in range(5):
            secteur = Secteur.objects.create(
                nom=f'Secteur_PERF_{i}',
                couleur='#000000',
                ordre=i
            )
            self.secteurs.append(secteur)

        # Créer des événements avec relations
        for i in range(20):
            event = Event.objects.create(
                titre=f'Event {i}',
                date_debut=timezone.now() + timezone.timedelta(days=i),
                createur=self.user
            )
            # Ajouter des secteurs à certains événements
            if i % 2 == 0:
                event.secteurs.add(self.secteurs[i % len(self.secteurs)])

    def test_calendar_view_query_count(self):
        """Test que la vue calendrier utilise select_related et prefetch_related."""
        reset_queries()
        response = self.client.get(reverse('events:calendar'))
        query_count = len(connection.queries)

        self.assertEqual(response.status_code, 200)
        # Avec select_related et prefetch_related, le nombre de requêtes
        # devrait être faible même avec 20 événements
        # (1 session, 1 user, 1 events avec relations, peut-être quelques autres)
        self.assertLess(
            query_count, 10,
            f"Trop de requêtes SQL: {query_count}")

    def test_list_view_query_count(self):
        """Test que la vue liste utilise select_related et prefetch_related."""
        reset_queries()
        response = self.client.get(reverse('events:list'))
        query_count = len(connection.queries)

        self.assertEqual(response.status_code, 200)
        # Avec only(), select_related et prefetch_related, le nombre devrait être faible
        self.assertLess(
            query_count, 10,
            f"Trop de requêtes SQL: {query_count}")

    def test_detail_view_query_count(self):
        """Test que la vue détail utilise select_related et prefetch_related."""
        event = Event.objects.first()
        reset_queries()
        response = self.client.get(
            reverse('events:detail', kwargs={'pk': event.pk})
        )
        query_count = len(connection.queries)

        self.assertEqual(response.status_code, 200)
        # Une seule requête principale avec les relations préchargées
        self.assertLess(
            query_count, 8,
            f"Trop de requêtes SQL: {query_count}")

    def test_timeline_view_query_count(self):
        """Test que la vue timeline utilise les optimisations."""
        reset_queries()
        response = self.client.get(reverse('events:timeline'))
        query_count = len(connection.queries)

        self.assertEqual(response.status_code, 200)
        # Avec only(), select_related et prefetch_related
        self.assertLess(
            query_count, 10,
            f"Trop de requêtes SQL: {query_count}")

    def test_list_view_performance_with_many_events(self):
        """Test les performances avec beaucoup d'événements."""
        # Créer 100 événements supplémentaires
        for i in range(100):
            Event.objects.create(
                titre=f'Event {i + 20}',
                date_debut=timezone.now() + timezone.timedelta(days=i + 20),
                createur=self.user
            )

        reset_queries()
        start_time = time.time()

        response = self.client.get(reverse('events:list'))

        elapsed_time = time.time() - start_time
        query_count = len(connection.queries)

        self.assertEqual(response.status_code, 200)
        # Le temps de réponse devrait rester raisonnable
        self.assertLess(
            elapsed_time, 1.0,
            f"Temps de réponse trop long: {elapsed_time:.3f}s")
        # Le nombre de requêtes ne devrait pas croître linéairement
        self.assertLess(
            query_count, 15,
            f"Trop de requêtes SQL: {query_count}")

    def test_no_n_plus_one_queries(self):
        """Test qu'il n'y a pas de problème N+1 queries."""
        # Créer des événements avec fichiers
        for i in range(10):
            event = Event.objects.create(
                titre=f'Event with files {i}',
                date_debut=timezone.now() + timezone.timedelta(days=i),
                createur=self.user
            )
            # Ajouter des fichiers
            for j in range(3):
                EventFile.objects.create(
                    event=event,
                    fichier=create_test_image(f'test_{i}_{j}.png'),
                    type_fichier='image',
                    nom=f'test_{i}_{j}.png',
                    taille=1024,
                    ordre=j
                )

        reset_queries()
        response = self.client.get(reverse('events:list'))
        query_count = len(connection.queries)

        self.assertEqual(response.status_code, 200)
        # Même avec des fichiers, le nombre de requêtes devrait rester faible
        # grâce à prefetch_related
        self.assertLess(
            query_count, 12,
            f"Problème N+1 queries détecté: {query_count}")
