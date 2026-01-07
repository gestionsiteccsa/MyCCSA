"""
Tests de sécurité pour l'application events.
"""
import os
from io import BytesIO
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from PIL import Image
from .models import Event, EventFile
from .forms import EventFileForm
from .constants import MAX_FILE_SIZE, ALLOWED_IMAGE_TYPES, ALLOWED_PDF_TYPES

User = get_user_model()


def create_test_image(filename='test.png', size=(100, 100), format='PNG'):
    """
    Crée une image de test.

    Args:
        filename: Nom du fichier
        size: Taille de l'image (width, height)
        format: Format de l'image (PNG, JPEG, etc.)

    Returns:
        SimpleUploadedFile: Fichier image pour les tests
    """
    image = Image.new('RGB', size, color='red')
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return SimpleUploadedFile(
        filename,
        buffer.read(),
        content_type=f'image/{format.lower()}'
    )


def create_fake_pdf(filename='fake.pdf'):
    """
    Crée un faux fichier PDF pour tester la validation.

    Args:
        filename: Nom du fichier

    Returns:
        SimpleUploadedFile: Fichier pour les tests
    """
    # Créer un fichier qui n'est pas un vrai PDF
    fake_content = b'This is not a PDF file'
    return SimpleUploadedFile(
        filename,
        fake_content,
        content_type='application/pdf'
    )


class EventFileFormSecurityTest(TestCase):
    """
    Tests de sécurité pour EventFileForm.
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

    def test_validation_mime_type_image_real_content(self):
        """
        Test que la validation vérifie le contenu réel de l'image, pas seulement le MIME.

        Vérifie que Pillow peut ouvrir et valider l'image.
        """
        # Créer une vraie image PNG
        image_file = create_test_image('test.png', format='PNG')
        # Créer une instance EventFile pour le formulaire
        event_file = EventFile(event=self.event, ordre=0)
        form = EventFileForm({'ordre': 0}, {'fichier': image_file}, instance=event_file)

        # Le formulaire devrait être valide pour le fichier
        # (même si l'instance complète ne peut pas être sauvegardée sans event)
        self.assertTrue(form.is_valid())

    def test_validation_mime_type_fake_pdf(self):
        """
        Test que la validation détecte un faux PDF (falsification du content_type).

        Un fichier avec content_type='application/pdf' mais qui n'est pas un vrai PDF
        devrait être rejeté.
        """
        # Créer un faux PDF (fichier texte avec content_type PDF)
        fake_pdf = create_fake_pdf('fake.pdf')
        form = EventFileForm({}, {'fichier': fake_pdf})

        # Le formulaire devrait être invalide car le fichier n'est pas un vrai PDF
        self.assertFalse(form.is_valid())
        self.assertIn('fichier', form.errors)

    def test_validation_file_size_exceeded(self):
        """
        Test que la validation rejette les fichiers trop volumineux.
        """
        # Créer un fichier qui dépasse la taille maximale
        large_content = b'x' * (MAX_FILE_SIZE + 1)
        large_file = SimpleUploadedFile(
            'large.png',
            large_content,
            content_type='image/png'
        )
        form = EventFileForm({}, {'fichier': large_file})

        # Le formulaire devrait être invalide
        self.assertFalse(form.is_valid())
        self.assertIn('fichier', form.errors)
        # Vérifier que l'erreur mentionne la taille
        error_str = str(form.errors['fichier']).lower()
        self.assertTrue('volumineux' in error_str or 'taille' in error_str or 'size' in error_str)

    def test_validation_file_type_not_allowed(self):
        """
        Test que la validation rejette les types de fichiers non autorisés.
        """
        # Créer un fichier avec un type non autorisé
        forbidden_file = SimpleUploadedFile(
            'script.exe',
            b'fake executable content',
            content_type='application/x-msdownload'  # Type EXE
        )
        form = EventFileForm({}, {'fichier': forbidden_file})

        # Le formulaire devrait être invalide
        self.assertFalse(form.is_valid())
        self.assertIn('fichier', form.errors)
        # Vérifier que l'erreur mentionne le type non autorisé
        error_str = str(form.errors['fichier']).lower()
        self.assertTrue('non autorisé' in error_str or 'non autorise' in error_str or 'not allowed' in error_str)

    def test_validation_corrupted_image(self):
        """
        Test que la validation détecte les images corrompues.
        """
        # Créer un fichier qui prétend être une image mais qui est corrompu
        corrupted_content = b'This is not a valid image file'
        corrupted_file = SimpleUploadedFile(
            'corrupted.png',
            corrupted_content,
            content_type='image/png'
        )
        form = EventFileForm({}, {'fichier': corrupted_file})

        # Le formulaire devrait être invalide
        self.assertFalse(form.is_valid())
        self.assertIn('fichier', form.errors)


class EventViewSecurityTest(TestCase):
    """
    Tests de sécurité pour les vues events.
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

        self.event = Event.objects.create(
            titre='Test Event',
            date_debut=timezone.now() + timezone.timedelta(days=1),
            createur=self.user
        )

    def test_rate_limiting_uploads(self):
        """
        Test que le rate limiting fonctionne pour les uploads.

        Après avoir uploadé MAX_UPLOADS fichiers, les uploads suivants
        devraient être bloqués.
        """
        from .constants import RATE_LIMIT_UPLOADS_PER_MINUTE

        # Vider le cache avant le test
        cache.clear()

        # Uploader plusieurs fichiers rapidement
        for i in range(RATE_LIMIT_UPLOADS_PER_MINUTE + 1):
            image_file = create_test_image(f'test_{i}.png')
            data = {
                'titre': f'Event {i}',
                'date_debut': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
                'timezone': 'Europe/Paris',
                'adresse_ville': 'Paris',
            }
            files = {'images': [image_file]}

            response = self.client.post(reverse('events:create'), data, files=files)

            if i < RATE_LIMIT_UPLOADS_PER_MINUTE:
                # Les premiers uploads devraient réussir
                self.assertIn(response.status_code, [200, 302])
            else:
                # Le dernier upload devrait être bloqué (429 Too Many Requests)
                self.assertEqual(response.status_code, 429)

    def test_file_size_validation_in_view(self):
        """
        Test que la validation de taille est effectuée dans la vue également.

        Même si le formulaire passe, la vue devrait vérifier la taille.
        """
        # Créer un fichier trop volumineux
        large_content = b'x' * (MAX_FILE_SIZE + 1)
        large_file = SimpleUploadedFile(
            'large.png',
            large_content,
            content_type='image/png'
        )

        data = {
            'titre': 'Test Event',
            'date_debut': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'timezone': 'Europe/Paris',
            'adresse_ville': 'Paris',
        }
        files = {'images': [large_file]}

        self.client.post(reverse('events:create'), data, files=files)

        # La vue devrait rejeter le fichier trop volumineux
        # Le formulaire devrait rejeter le fichier avant même d'arriver à la validation de la vue
        # Donc on vérifie que l'événement n'a pas été créé
        self.assertFalse(Event.objects.filter(titre='Test Event').exists())

    def test_csrf_protection(self):
        """
        Test que les formulaires POST sont protégés par CSRF.
        """
        # Créer un client sans CSRF
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)

        data = {
            'titre': 'Test Event',
            'date_debut': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'timezone': 'Europe/Paris',
            'adresse_ville': 'Paris',
        }

        # Tenter de créer un événement sans token CSRF
        response = csrf_client.post(reverse('events:create'), data)

        # Devrait échouer avec une erreur CSRF (403)
        self.assertEqual(response.status_code, 403)

    def test_permission_check_create_event(self):
        """
        Test que seuls les utilisateurs autorisés peuvent créer des événements.
        """
        # Créer un utilisateur sans permissions
        unauthorized_user = User.objects.create_user(
            email='unauthorized@example.com',
            password='testpass123'
        )
        self.client.force_login(unauthorized_user)

        data = {
            'titre': 'Test Event',
            'date_debut': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'timezone': 'Europe/Paris',
            'adresse_ville': 'Paris',
        }

        response = self.client.post(reverse('events:create'), data)

        # Devrait rediriger vers la page de connexion ou retourner 403
        self.assertIn(response.status_code, [302, 403])

    def test_permission_check_update_own_event(self):
        """
        Test qu'un utilisateur ne peut modifier que ses propres événements.
        """
        # Créer un autre utilisateur
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            email_verified=True
        )
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(Event)
        permission = Permission.objects.get(
            codename='change_event',
            content_type=content_type
        )
        other_user.user_permissions.add(permission)
        self.client.force_login(other_user)

        # Tenter de modifier l'événement créé par self.user
        data = {
            'titre': 'Modified Event',
            'date_debut': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'timezone': 'Europe/Paris',
            'adresse_ville': 'Paris',
        }

        response = self.client.post(
            reverse('events:update', kwargs={'pk': self.event.pk}),
            data
        )

        # Devrait rediriger vers la page de détail avec un message d'erreur
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('events:detail', kwargs={'pk': self.event.pk}))
