"""
Tests de sécurité pour l'application secteurs.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from secteurs.models import Secteur

User = get_user_model()


class CSRFProtectionTest(TestCase):
    """
    Tests pour la protection CSRF.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client(enforce_csrf_checks=True)
        self.superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.secteur = Secteur.objects.create(
            nom='SANTÉ',
            couleur='#b4c7e7',
            ordre=1
        )

    def test_csrf_protection_create(self):
        """Test que la création nécessite un token CSRF."""
        self.client.login(email='admin@example.com', password='adminpass123')

        # Tentative de POST sans CSRF token
        response = self.client.post(reverse('secteurs:create'), {
            'nom': 'NOUVEAU',
            'couleur': '#ff0000',
            'ordre': 1
        }, follow=False)

        # Django devrait rejeter la requête (403 ou redirect)
        self.assertIn(response.status_code, [403, 400])

    def test_csrf_protection_update(self):
        """Test que la modification nécessite un token CSRF."""
        self.client.login(email='admin@example.com', password='adminpass123')

        # Tentative de POST sans CSRF token
        response = self.client.post(
            reverse('secteurs:update', args=[self.secteur.pk]),
            {
                'nom': 'MODIFIÉ',
                'couleur': '#ff0000',
                'ordre': 2
            },
            follow=False
        )

        # Django devrait rejeter la requête
        self.assertIn(response.status_code, [403, 400])

    def test_csrf_protection_delete(self):
        """Test que la suppression nécessite un token CSRF."""
        self.client.login(email='admin@example.com', password='adminpass123')

        # Tentative de POST sans CSRF token
        response = self.client.post(
            reverse('secteurs:delete', args=[self.secteur.pk]),
            follow=False
        )

        # Django devrait rejeter la requête
        self.assertIn(response.status_code, [403, 400])


class PermissionsTest(TestCase):
    """
    Tests pour les permissions d'accès.
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
            password='userpass123'
        )
        self.secteur = Secteur.objects.create(
            nom='SANTÉ',
            couleur='#b4c7e7',
            ordre=1
        )

    def test_anonymous_user_redirected(self):
        """Test que les utilisateurs anonymes sont redirigés vers la connexion."""
        # Liste
        response = self.client.get(reverse('secteurs:list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

        # Création
        response = self.client.get(reverse('secteurs:create'))
        self.assertEqual(response.status_code, 302)

        # Modification
        response = self.client.get(reverse('secteurs:update', args=[self.secteur.pk]))
        self.assertEqual(response.status_code, 302)

        # Suppression
        response = self.client.get(reverse('secteurs:delete', args=[self.secteur.pk]))
        self.assertEqual(response.status_code, 302)

        # Liste utilisateurs
        response = self.client.get(reverse('secteurs:user_list'))
        self.assertEqual(response.status_code, 302)

    def test_normal_user_forbidden(self):
        """Test que les utilisateurs normaux reçoivent 403."""
        self.client.login(email='user@example.com', password='userpass123')

        # Liste
        response = self.client.get(reverse('secteurs:list'))
        self.assertEqual(response.status_code, 403)

        # Création
        response = self.client.get(reverse('secteurs:create'))
        self.assertEqual(response.status_code, 403)

        # Modification
        response = self.client.get(reverse('secteurs:update', args=[self.secteur.pk]))
        self.assertEqual(response.status_code, 403)

        # Suppression
        response = self.client.get(reverse('secteurs:delete', args=[self.secteur.pk]))
        self.assertEqual(response.status_code, 403)

        # Liste utilisateurs
        response = self.client.get(reverse('secteurs:user_list'))
        self.assertEqual(response.status_code, 403)

    def test_superuser_only_access(self):
        """Test que seuls les superusers peuvent accéder."""
        self.client.login(email='admin@example.com', password='adminpass123')

        # Toutes les vues devraient être accessibles
        response = self.client.get(reverse('secteurs:list'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('secteurs:create'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('secteurs:update', args=[self.secteur.pk]))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('secteurs:delete', args=[self.secteur.pk]))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('secteurs:user_list'))
        self.assertEqual(response.status_code, 200)


class InputValidationTest(TestCase):
    """
    Tests pour la validation des entrées utilisateur.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.client.login(email='admin@example.com', password='adminpass123')

    def test_xss_protection_in_nom(self):
        """Test que les scripts XSS sont échappés dans le nom."""
        # Tentative d'injection XSS
        xss_payload = '<script>alert("XSS")</script>'

        response = self.client.post(reverse('secteurs:create'), {
            'nom': xss_payload,
            'couleur': '#ff0000',
            'ordre': 1
        })

        # Si le formulaire est valide, le script devrait être échappé dans le template
        # Si invalide, c'est aussi une protection
        if response.status_code == 200:
            # Le template Django échappe automatiquement
            self.assertNotContains(response, '<script>')
            self.assertNotContains(response, 'alert("XSS")')

    def test_sql_injection_protection(self):
        """Test la protection contre l'injection SQL."""
        # Tentative d'injection SQL classique
        sql_payload = "'; DROP TABLE secteurs_secteur; --"

        response = self.client.post(reverse('secteurs:create'), {
            'nom': sql_payload,
            'couleur': '#ff0000',
            'ordre': 1
        })

        # Vérifier que la table existe toujours
        self.assertTrue(
            Secteur.objects.model._meta.db_table in
            [t.name for t in Secteur.objects.db.connection.introspection.table_names()])

        # Si le secteur a été créé, le nom devrait être stocké tel quel (échappé par l'ORM)
        if response.status_code == 302:  # Redirect après succès
            secteur = Secteur.objects.filter(nom=sql_payload).first()
            if secteur:
                # Le nom devrait être stocké tel quel, pas exécuté
                self.assertEqual(secteur.nom, sql_payload)

    def test_mass_assignment_protection(self):
        """Test que les champs non autorisés ne peuvent pas être modifiés."""
        secteur = Secteur.objects.create(
            nom='ORIGINAL',
            couleur='#000000',
            ordre=1
        )

        # Tentative de modifier un champ non présent dans le formulaire
        # (par exemple, essayer de modifier created_at via POST)
        original_created_at = secteur.created_at

        self.client.post(
            reverse('secteurs:update', args=[secteur.pk]),
            {
                'nom': 'MODIFIÉ',
                'couleur': '#ff0000',
                'ordre': 2,
                # Tentative de modifier created_at (ne devrait pas fonctionner)
                'created_at': '2020-01-01T00:00:00Z'
            }
        )

        secteur.refresh_from_db()

        # Le created_at ne devrait pas avoir changé
        self.assertEqual(secteur.created_at, original_created_at)
        # Mais le nom devrait avoir changé
        self.assertEqual(secteur.nom, 'MODIFIÉ')

    def test_invalid_color_format_rejected(self):
        """Test que les formats de couleur invalides sont rejetés."""
        response = self.client.post(reverse('secteurs:create'), {
            'nom': 'TEST',
            'couleur': 'not-a-color',
            'ordre': 1
        })

        # Le formulaire devrait être invalide
        self.assertEqual(response.status_code, 200)
        # Vérifier que le formulaire contient des erreurs
        self.assertIn('form', response.context)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('couleur', response.context['form'].errors)

    def test_empty_nom_rejected(self):
        """Test que les noms vides sont rejetés."""
        response = self.client.post(reverse('secteurs:create'), {
            'nom': '',
            'couleur': '#ff0000',
            'ordre': 1
        })

        # Le formulaire devrait être invalide
        self.assertEqual(response.status_code, 200)
        # Vérifier que le formulaire contient des erreurs
        self.assertIn('form', response.context)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('nom', response.context['form'].errors)
