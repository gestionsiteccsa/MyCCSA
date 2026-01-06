"""
Tests pour les templates de l'application secteurs.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from secteurs.models import Secteur

User = get_user_model()


class ListTemplateTest(TestCase):
    """
    Tests pour le template de liste des secteurs.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.secteur = Secteur.objects.create(
            nom='SANTÉ',
            couleur='#b4c7e7',
            ordre=1
        )
        self.client.login(email='admin@example.com', password='adminpass123')

    def test_list_template_no_user_count(self):
        """Test que le template n'affiche plus le nombre d'utilisateurs."""
        response = self.client.get(reverse('secteurs:list'))
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que le compteur d'utilisateurs n'est pas présent
        self.assertNotContains(response, 'utilisateur')
        self.assertNotContains(response, 'utilisateurs')
        self.assertNotContains(response, 'utilisateurs.count')
        
        # Vérifier qu'il n'y a pas de référence au count dans le HTML
        content = response.content.decode('utf-8')
        # Ne devrait pas contenir de pattern comme "X utilisateur(s)"
        import re
        pattern = r'\d+\s+utilisateur'
        self.assertIsNone(re.search(pattern, content, re.IGNORECASE),
                         "Le template contient encore une référence au nombre d'utilisateurs")

    def test_list_template_displays_required_fields(self):
        """Test que le template affiche les champs requis."""
        response = self.client.get(reverse('secteurs:list'))
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que le nom est affiché
        self.assertContains(response, 'SANTÉ')
        
        # Vérifier que la couleur est affichée (code hex)
        self.assertContains(response, '#b4c7e7')
        
        # Vérifier que les boutons sont présents
        self.assertContains(response, 'Modifier')
        self.assertContains(response, 'Supprimer')

    def test_list_template_buttons_present(self):
        """Test que les boutons Modifier et Supprimer sont présents."""
        response = self.client.get(reverse('secteurs:list'))
        self.assertEqual(response.status_code, 200)
        
        # Vérifier la présence des boutons avec leurs liens
        update_url = reverse('secteurs:update', args=[self.secteur.pk])
        delete_url = reverse('secteurs:delete', args=[self.secteur.pk])
        
        self.assertContains(response, update_url)
        self.assertContains(response, delete_url)
        
        # Vérifier que les boutons ont les bonnes classes/attributs
        content = response.content.decode('utf-8')
        # Les boutons devraient avoir des aria-label
        self.assertIn('aria-label', content.lower())

    def test_list_template_csrf_token_present(self):
        """Test que les formulaires contiennent le token CSRF."""
        # Note: La liste n'a pas de formulaire, mais vérifions les autres templates
        # via les vues qui les utilisent
        
        # Test pour le formulaire de création
        response = self.client.get(reverse('secteurs:create'))
        self.assertContains(response, 'csrfmiddlewaretoken')
        
        # Test pour le formulaire de modification
        response = self.client.get(reverse('secteurs:update', args=[self.secteur.pk]))
        self.assertContains(response, 'csrfmiddlewaretoken')
        
        # Test pour le formulaire de suppression
        response = self.client.get(reverse('secteurs:delete', args=[self.secteur.pk]))
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_list_template_aria_labels(self):
        """Test que les éléments interactifs ont des attributs ARIA."""
        response = self.client.get(reverse('secteurs:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # Vérifier la présence d'attributs ARIA pour l'accessibilité
        # Les boutons devraient avoir aria-label
        self.assertIn('aria-label', content.lower())

    def test_list_template_responsive_structure(self):
        """Test que le template a une structure responsive."""
        response = self.client.get(reverse('secteurs:list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode('utf-8')
        
        # Vérifier la présence de classes Tailwind responsive
        # (flex, grid, etc.)
        self.assertIn('grid', content.lower() or 'flex' in content.lower())












