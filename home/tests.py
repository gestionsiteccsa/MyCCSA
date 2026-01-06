"""
Tests de l'application home.
"""
from django.test import TestCase, Client
from django.urls import reverse
from .models import ExampleModel


class HomeViewTest(TestCase):
    """
    Tests pour la vue home.
    """
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.client = Client()

    def test_home_view_status_code(self):
        """Test que la vue home retourne un code 200."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_home_view_template(self):
        """Test que la vue home utilise le bon template."""
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'home/index.html')

    def test_home_view_contains_title(self):
        """Test que la vue home contient le titre."""
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Bienvenue')


class ExampleModelTest(TestCase):
    """
    Tests pour le modèle ExampleModel.
    """
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.example = ExampleModel.objects.create(
            name="Test Example",
            description="Description de test",
            is_active=True
        )

    def test_example_model_str(self):
        """Test la méthode __str__ du modèle."""
        self.assertEqual(str(self.example), "Test Example")

    def test_example_model_created_at(self):
        """Test que created_at est automatiquement défini."""
        self.assertIsNotNone(self.example.created_at)

    def test_example_model_updated_at(self):
        """Test que updated_at est automatiquement défini."""
        self.assertIsNotNone(self.example.updated_at)

    def test_example_model_default_is_active(self):
        """Test que is_active est True par défaut."""
        new_example = ExampleModel.objects.create(name="New Example")
        self.assertTrue(new_example.is_active)
