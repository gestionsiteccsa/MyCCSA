"""
Tests unitaires pour les modèles de l'application secteurs.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from secteurs.models import Secteur

User = get_user_model()


class SecteurModelTest(TestCase):
    """
    Tests pour le modèle Secteur.
    """
    def setUp(self):
        """Configuration initiale."""
        self.secteur, _ = Secteur.objects.get_or_create(
            nom='SANTÉ_TEST_MODELS',
            defaults={
                'couleur': '#b4c7e7',
                'ordre': 100
            }
        )

    def test_secteur_str(self):
        """Test la représentation string du secteur."""
        self.assertEqual(str(self.secteur), 'SANTÉ')

    def test_secteur_nom_unique(self):
        """Test que le nom du secteur doit être unique."""
        with self.assertRaises(Exception):
            Secteur.objects.create(
                nom='SANTÉ_TEST_MODELS',  # Utiliser le même nom que dans setUp
                couleur='#ff0000',
                ordre=2
            )

    def test_secteur_ordre_default(self):
        """Test que l'ordre par défaut est 0."""
        secteur, _ = Secteur.objects.get_or_create(
            nom='NOUVEAU_TEST_MODELS',
            defaults={'couleur': '#000000'}
        )
        self.assertEqual(secteur.ordre, 0)

    def test_secteur_ordering(self):
        """Test l'ordre de tri des secteurs."""
        secteur1, _ = Secteur.objects.get_or_create(
            nom='RURALITÉ_TEST_ORDERING',
            defaults={'couleur': '#005b24', 'ordre': 2}
        )
        secteur2, _ = Secteur.objects.get_or_create(
            nom='AUTRE_TEST_ORDERING',
            defaults={'couleur': '#ff0000', 'ordre': 1}
        )

        secteurs = list(Secteur.objects.all())
        self.assertEqual(secteurs[0].nom, 'SANTÉ')
        self.assertEqual(secteurs[1].nom, 'AUTRE')
        self.assertEqual(secteurs[2].nom, 'RURALITÉ')


class UserSecteursRelationTest(TestCase):
    """
    Tests pour la relation ManyToMany entre User et Secteur.
    """
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.secteur1, _ = Secteur.objects.get_or_create(
            nom='SANTÉ_TEST_RELATION',
            defaults={'couleur': '#b4c7e7', 'ordre': 1}
        )
        self.secteur2, _ = Secteur.objects.get_or_create(
            nom='RURALITÉ_TEST_RELATION',
            defaults={'couleur': '#005b24', 'ordre': 2}
        )

    def test_user_add_secteur(self):
        """Test l'ajout d'un secteur à un utilisateur."""
        self.user.secteurs.add(self.secteur1)
        self.assertIn(self.secteur1, self.user.secteurs.all())

    def test_user_add_multiple_secteurs(self):
        """Test l'ajout de plusieurs secteurs à un utilisateur."""
        self.user.secteurs.add(self.secteur1, self.secteur2)
        self.assertEqual(self.user.secteurs.count(), 2)

    def test_user_remove_secteur(self):
        """Test la suppression d'un secteur d'un utilisateur."""
        self.user.secteurs.add(self.secteur1, self.secteur2)
        self.user.secteurs.remove(self.secteur1)
        self.assertNotIn(self.secteur1, self.user.secteurs.all())
        self.assertIn(self.secteur2, self.user.secteurs.all())

    def test_secteur_utilisateurs_related_name(self):
        """Test que le related_name 'utilisateurs' fonctionne."""
        self.user.secteurs.add(self.secteur1)
        self.assertIn(self.user, self.secteur1.utilisateurs.all())

    def test_user_secteurs_empty(self):
        """Test qu'un utilisateur peut n'avoir aucun secteur."""
        self.assertEqual(self.user.secteurs.count(), 0)
