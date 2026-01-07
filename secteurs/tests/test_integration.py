"""
Tests d'intégration pour l'application secteurs.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from secteurs.models import Secteur

User = get_user_model()


class SecteurCRUDIntegrationTest(TestCase):
    """
    Tests d'intégration pour le CRUD complet des secteurs.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.client.login(email='admin@example.com', password='adminpass123')

    def test_full_crud_cycle(self):
        """Test un cycle complet CRUD."""
        # CREATE
        response = self.client.post(reverse('secteurs:create'), {
            'nom': 'NOUVEAU SECTEUR',
            'couleur': '#ff0000',
            'ordre': 1
        })
        self.assertRedirects(response, reverse('secteurs:list'))
        secteur = Secteur.objects.get(nom='NOUVEAU SECTEUR')
        self.assertEqual(secteur.couleur, '#FF0000')

        # READ
        response = self.client.get(reverse('secteurs:list'))
        self.assertContains(response, 'NOUVEAU SECTEUR')

        # UPDATE
        response = self.client.post(
            reverse('secteurs:update', args=[secteur.pk]),
            {
                'nom': 'SECTEUR MODIFIÉ',
                'couleur': '#00ff00',
                'ordre': 2
            }
        )
        self.assertRedirects(response, reverse('secteurs:list'))
        secteur.refresh_from_db()
        self.assertEqual(secteur.nom, 'SECTEUR MODIFIÉ')

        # DELETE
        response = self.client.post(
            reverse('secteurs:delete', args=[secteur.pk])
        )
        self.assertRedirects(response, reverse('secteurs:list'))
        self.assertFalse(Secteur.objects.filter(pk=secteur.pk).exists())


class UserSecteursIntegrationTest(TestCase):
    """
    Tests d'intégration pour l'attribution de secteurs aux utilisateurs.
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
            password='userpass123',
            first_name='John',
            last_name='Doe'
        )
        self.secteur1, _ = Secteur.objects.get_or_create(
            nom='SANTÉ_TEST_INTEGRATION',
            defaults={'couleur': '#b4c7e7', 'ordre': 105}
        )
        self.secteur2, _ = Secteur.objects.get_or_create(
            nom='RURALITÉ_TEST_INTEGRATION',
            defaults={'couleur': '#005b24', 'ordre': 106}
        )
        self.client.login(email='admin@example.com', password='adminpass123')

    def test_assign_secteurs_to_user(self):
        """Test l'attribution complète de secteurs à un utilisateur."""
        # Attribuer des secteurs
        response = self.client.post(
            reverse('secteurs:user_secteurs', args=[self.user.pk]),
            {
                'secteurs': [self.secteur1.pk, self.secteur2.pk]
            }
        )
        self.assertRedirects(
            response,
            reverse('secteurs:user_secteurs', args=[self.user.pk])
        )

        # Vérifier que les secteurs sont bien attribués
        self.user.refresh_from_db()
        self.assertEqual(self.user.secteurs.count(), 2)
        self.assertIn(self.secteur1, self.user.secteurs.all())
        self.assertIn(self.secteur2, self.user.secteurs.all())

        # Vérifier dans la liste des utilisateurs
        response = self.client.get(reverse('secteurs:user_list'))
        self.assertContains(response, 'SANTÉ')
        self.assertContains(response, 'RURALITÉ')

    def test_modify_user_secteurs(self):
        """Test la modification des secteurs d'un utilisateur."""
        # Attribuer initialement secteur1
        self.user.secteurs.add(self.secteur1)

        # Modifier pour avoir seulement secteur2
        response = self.client.post(
            reverse('secteurs:user_secteurs', args=[self.user.pk]),
            {
                'secteurs': [self.secteur2.pk]
            }
        )
        self.assertRedirects(
            response,
            reverse('secteurs:user_secteurs', args=[self.user.pk])
        )

        # Vérifier la modification
        self.user.refresh_from_db()
        self.assertEqual(self.user.secteurs.count(), 1)
        self.assertNotIn(self.secteur1, self.user.secteurs.all())
        self.assertIn(self.secteur2, self.user.secteurs.all())

