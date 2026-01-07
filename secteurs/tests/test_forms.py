"""
Tests unitaires pour les formulaires de l'application secteurs.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from secteurs.forms import SecteurForm, UserSecteursForm
from secteurs.models import Secteur

User = get_user_model()


class SecteurFormTest(TestCase):
    """
    Tests pour le formulaire SecteurForm.
    """
    def test_valid_form(self):
        """Test un formulaire valide."""
        form_data = {
            'nom': 'NOUVEAU_SECTEUR_TEST',
            'couleur': '#b4c7e7',
            'ordre': 1
        }
        form = SecteurForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Erreurs du formulaire: {form.errors}")

    def test_invalid_couleur_format(self):
        """Test la validation du format de couleur."""
        form_data = {
            'nom': 'TEST_INVALID_COLOR',
            'couleur': 'invalid',
            'ordre': 1
        }
        form = SecteurForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('couleur', form.errors)

    def test_couleur_without_hash(self):
        """Test que la couleur peut être fournie sans #."""
        form_data = {
            'nom': 'TEST_COLOR_NO_HASH',
            'couleur': 'b4c7e7',
            'ordre': 1
        }
        form = SecteurForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['couleur'], '#B4C7E7')

    def test_couleur_normalization(self):
        """Test la normalisation de la couleur en majuscules."""
        form_data = {
            'nom': 'TEST_COLOR_NORM',
            'couleur': '#b4c7e7',
            'ordre': 1
        }
        form = SecteurForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['couleur'], '#B4C7E7')

    def test_nom_too_short(self):
        """Test la validation de la longueur minimale du nom."""
        form_data = {
            'nom': 'A',
            'couleur': '#b4c7e7',
            'ordre': 1
        }
        form = SecteurForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('nom', form.errors)

    def test_nom_stripped(self):
        """Test que les espaces sont supprimés du nom."""
        form_data = {
            'nom': '  TEST_STRIPPED  ',
            'couleur': '#b4c7e7',
            'ordre': 1
        }
        form = SecteurForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['nom'], 'TEST_STRIPPED')


class UserSecteursFormTest(TestCase):
    """
    Tests pour le formulaire UserSecteursForm.
    """
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.secteur1, _ = Secteur.objects.get_or_create(
            nom='TEST_FORM_SECTEUR1',
            defaults={
                'couleur': '#b4c7e7',
                'ordre': 1
            }
        )
        self.secteur2 = Secteur.objects.create(
            nom='RURALITÉ',
            couleur='#005b24',
            ordre=2
        )

    def test_form_initial_with_user_secteurs(self):
        """Test que le formulaire pré-remplit les secteurs de l'utilisateur."""
        self.user.secteurs.add(self.secteur1)
        form = UserSecteursForm(user=self.user)
        self.assertIn(self.secteur1.id, form.fields['secteurs'].initial)
        self.assertNotIn(self.secteur2.id, form.fields['secteurs'].initial)

    def test_form_secteurs_ordered(self):
        """Test que les secteurs sont ordonnés par ordre puis nom."""
        form = UserSecteursForm()
        secteurs = list(form.fields['secteurs'].queryset)
        # Vérifier que les secteurs sont ordonnés (peu importe les noms exacts)
        self.assertGreater(len(secteurs), 0)
        # Vérifier que l'ordre est respecté
        for i in range(len(secteurs) - 1):
            self.assertLessEqual(secteurs[i].ordre, secteurs[i + 1].ordre)

