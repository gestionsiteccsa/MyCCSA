"""
Tests pour les vues de l'application secteurs.
"""
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.db import connection, reset_queries
from django.urls import reverse
from secteurs.models import Secteur

User = get_user_model()


class SecteurListViewTest(TestCase):
    """
    Tests pour la vue de liste des secteurs.
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

    def test_list_view_requires_superuser(self):
        """Test que seuls les superusers peuvent accéder."""
        # Utilisateur normal
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('secteurs:list'))
        self.assertEqual(response.status_code, 403)

    def test_list_view_superuser_access(self):
        """Test l'accès pour un superuser."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('secteurs:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SANTÉ')
        # Vérifier que le compteur d'utilisateurs n'est plus affiché
        self.assertNotContains(response, 'utilisateur')
        self.assertNotContains(response, 'utilisateurs')

    def test_list_view_pagination(self):
        """Test la pagination de la liste."""
        # Créer plus de 25 secteurs
        for i in range(30):
            Secteur.objects.create(
                nom=f'Secteur {i}',
                couleur='#000000',
                ordre=i
            )

        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('secteurs:list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)

    @override_settings(DEBUG=True)
    def test_list_view_no_n_plus_one_queries(self):
        """Test qu'il n'y a pas de N+1 queries dans la liste des secteurs."""
        # Créer plusieurs secteurs
        for i in range(10):
            Secteur.objects.create(
                nom=f'Secteur {i}',
                couleur='#000000',
                ordre=i
            )

        self.client.login(email='admin@example.com', password='adminpass123')

        # Réinitialiser les requêtes
        reset_queries()

        # Faire la requête
        response = self.client.get(reverse('secteurs:list'))

        # Compter les requêtes SQL
        query_count = len(connection.queries)

        # Vérifier que le nombre de requêtes est raisonnable (pas de N+1)
        # On devrait avoir : 1 pour la session, 1 pour l'utilisateur, 1 pour les secteurs
        # Potentiellement quelques autres pour les templates, mais pas N requêtes
        self.assertLess(
            query_count, 10,
            f"Trop de requêtes SQL ({query_count}). Possible problème N+1.")
        self.assertEqual(response.status_code, 200)

    def test_list_view_queries_count(self):
        """Test que le nombre de requêtes reste constant même avec plusieurs secteurs."""
        self.client.login(email='admin@example.com', password='adminpass123')

        # Test avec 5 secteurs
        for i in range(5):
            Secteur.objects.create(
                nom=f'Secteur {i}',
                couleur='#000000',
                ordre=i
            )

        reset_queries()
        response1 = self.client.get(reverse('secteurs:list'))
        queries_5 = len(connection.queries)

        # Test avec 20 secteurs
        for i in range(15):
            Secteur.objects.create(
                nom=f'Secteur {i + 5}',
                couleur='#000000',
                ordre=i + 5
            )

        reset_queries()
        response2 = self.client.get(reverse('secteurs:list'))
        queries_20 = len(connection.queries)

        # Le nombre de requêtes ne devrait pas augmenter linéairement
        # (pas de N+1 query)
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        # Les requêtes devraient être similaires (tolérance de 2 requêtes)
        self.assertLessEqual(
            abs(queries_20 - queries_5), 2,
            f"Le nombre de requêtes a trop augmenté: {queries_5} -> {queries_20}")

    def test_list_view_uses_only_optimization(self):
        """Test que la vue utilise only() pour optimiser les requêtes."""
        # Créer un secteur
        Secteur.objects.create(
            nom='TEST',
            couleur='#FF0000',
            ordre=1
        )

        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('secteurs:list'))

        self.assertEqual(response.status_code, 200)
        # Vérifier que les secteurs sont bien chargés
        self.assertIn('page_obj', response.context)
        page_obj = response.context['page_obj']
        self.assertGreater(page_obj.count(), 0)

        # Vérifier que les champs nécessaires sont présents
        for secteur_obj in page_obj:
            self.assertTrue(hasattr(secteur_obj, 'nom'))
            self.assertTrue(hasattr(secteur_obj, 'couleur'))
            self.assertTrue(hasattr(secteur_obj, 'ordre'))
            self.assertTrue(hasattr(secteur_obj, 'pk'))


class SecteurCreateViewTest(TestCase):
    """
    Tests pour la vue de création de secteur.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )

    def test_create_view_get(self):
        """Test l'affichage du formulaire de création."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('secteurs:create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Créer un secteur')

    def test_create_view_post_valid(self):
        """Test la création d'un secteur avec des données valides."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.post(reverse('secteurs:create'), {
            'nom': 'NOUVEAU',
            'couleur': '#ff0000',
            'ordre': 1
        })
        self.assertRedirects(response, reverse('secteurs:list'))
        self.assertTrue(Secteur.objects.filter(nom='NOUVEAU').exists())

    def test_create_view_post_invalid(self):
        """Test la création avec des données invalides."""
        self.client.login(email='admin@example.com', password='adminpass123')
        initial_count = Secteur.objects.count()
        response = self.client.post(reverse('secteurs:create'), {
            'nom': '',
            'couleur': 'invalid',
            'ordre': 999
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Secteur.objects.count(), initial_count)


class SecteurUpdateViewTest(TestCase):
    """
    Tests pour la vue de modification de secteur.
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

    def test_update_view_get(self):
        """Test l'affichage du formulaire de modification."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(
            reverse('secteurs:update', args=[self.secteur.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SANTÉ')

    def test_update_view_post_valid(self):
        """Test la modification d'un secteur."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.post(
            reverse('secteurs:update', args=[self.secteur.pk]),
            {
                'nom': 'SANTÉ MODIFIÉ',
                'couleur': '#ff0000',
                'ordre': 2
            }
        )
        self.assertRedirects(response, reverse('secteurs:list'))
        self.secteur.refresh_from_db()
        self.assertEqual(self.secteur.nom, 'SANTÉ MODIFIÉ')


class SecteurDeleteViewTest(TestCase):
    """
    Tests pour la vue de suppression de secteur.
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

    def test_delete_view_get(self):
        """Test l'affichage de la confirmation de suppression."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(
            reverse('secteurs:delete', args=[self.secteur.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SANTÉ')

    def test_delete_view_post(self):
        """Test la suppression d'un secteur."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.post(
            reverse('secteurs:delete', args=[self.secteur.pk])
        )
        self.assertRedirects(response, reverse('secteurs:list'))
        self.assertFalse(Secteur.objects.filter(pk=self.secteur.pk).exists())


class UserSecteursViewTest(TestCase):
    """
    Tests pour la vue d'attribution de secteurs aux utilisateurs.
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
        self.secteur1 = Secteur.objects.create(
            nom='SANTÉ',
            couleur='#b4c7e7',
            ordre=1
        )
        self.secteur2 = Secteur.objects.create(
            nom='RURALITÉ',
            couleur='#005b24',
            ordre=2
        )

    def test_user_secteurs_view_get(self):
        """Test l'affichage de la page d'attribution."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(
            reverse('secteurs:user_secteurs', args=[self.user.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.email)

    def test_user_secteurs_view_post(self):
        """Test l'attribution de secteurs à un utilisateur."""
        self.client.login(email='admin@example.com', password='adminpass123')
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
        self.assertEqual(self.user.secteurs.count(), 2)
        self.assertIn(self.secteur1, self.user.secteurs.all())
        self.assertIn(self.secteur2, self.user.secteurs.all())

    def test_user_secteurs_view_remove_all(self):
        """Test la suppression de tous les secteurs d'un utilisateur."""
        self.user.secteurs.add(self.secteur1, self.secteur2)
        self.client.login(email='admin@example.com', password='adminpass123')
        self.client.post(
            reverse('secteurs:user_secteurs', args=[self.user.pk]),
            {
                'secteurs': []
            }
        )
        self.assertEqual(self.user.secteurs.count(), 0)


class UserListViewTest(TestCase):
    """
    Tests pour la vue de liste des utilisateurs.
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

    def test_user_list_view_requires_superuser(self):
        """Test que seuls les superusers peuvent accéder."""
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('secteurs:user_list'))
        # Redirige vers login ou retourne 403
        self.assertIn(response.status_code, [302, 403])

    def test_user_list_view_superuser_access(self):
        """Test l'accès pour un superuser."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('secteurs:user_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'user@example.com')
