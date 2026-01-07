"""
Tests pour l'application role.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from .models import Role
from .forms import RoleForm, UserRoleForm

User = get_user_model()


class RoleModelTest(TestCase):
    """
    Tests pour le modèle Role.
    """
    def setUp(self):
        """Configuration initiale."""
        self.role = Role.objects.create(
            nom='Test Role',
            niveau=5
        )

    def test_role_str(self):
        """Test la représentation string du rôle."""
        self.assertEqual(str(self.role), 'Test Role')

    def test_role_nom_unique(self):
        """Test que le nom du rôle doit être unique."""
        with self.assertRaises(Exception):
            Role.objects.create(
                nom='Test Role',
                niveau=6
            )

    def test_role_niveau_unique(self):
        """Test que le niveau du rôle doit être unique."""
        with self.assertRaises(Exception):
            Role.objects.create(
                nom='Autre Role',
                niveau=5
            )

    def test_role_ordering(self):
        """Test l'ordre de tri des rôles."""
        Role.objects.create(
            nom='Autre Role',
            niveau=3
        )
        roles = list(Role.objects.all())
        self.assertEqual(roles[0].niveau, 3)
        self.assertEqual(roles[1].niveau, 5)


class RoleFormTest(TestCase):
    """
    Tests pour les formulaires de rôle.
    """
    def setUp(self):
        """Configuration initiale."""
        self.role = Role.objects.create(
            nom='Test Role',
            niveau=5
        )

    def test_role_form_valid(self):
        """Test un formulaire valide."""
        form = RoleForm(data={
            'nom': 'Nouveau Role',
            'niveau': 10
        })
        self.assertTrue(form.is_valid())

    def test_role_form_nom_too_short(self):
        """Test validation du nom trop court."""
        form = RoleForm(data={
            'nom': 'A',
            'niveau': 10
        })
        self.assertFalse(form.is_valid())

    def test_role_form_niveau_unique(self):
        """Test validation du niveau unique."""
        form = RoleForm(data={
            'nom': 'Autre Role',
            'niveau': 5  # Déjà utilisé
        })
        self.assertFalse(form.is_valid())

    def test_role_form_update_same_niveau(self):
        """Test qu'on peut modifier un rôle avec le même niveau."""
        form = RoleForm(data={
            'nom': 'Test Role Modifié',
            'niveau': 5
        }, instance=self.role)
        self.assertTrue(form.is_valid())


class UserRoleFormTest(TestCase):
    """
    Tests pour le formulaire d'assignation de rôle.
    """
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.role = Role.objects.create(
            nom='Test Role',
            niveau=5
        )

    def test_user_role_form_valid(self):
        """Test un formulaire valide."""
        form = UserRoleForm(data={
            'role': self.role.id
        }, user=self.user)
        self.assertTrue(form.is_valid())

    def test_user_role_form_no_role(self):
        """Test un formulaire sans rôle."""
        form = UserRoleForm(data={
            'role': ''
        }, user=self.user)
        self.assertTrue(form.is_valid())

    def test_user_role_form_initial(self):
        """Test que le formulaire pré-sélectionne le rôle de l'utilisateur."""
        self.user.role = self.role
        self.user.save()
        form = UserRoleForm(user=self.user)
        self.assertEqual(form.fields['role'].initial, self.role)


class RoleViewTest(TestCase):
    """
    Tests pour les vues de rôle.
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
        self.role = Role.objects.create(
            nom='Test Role',
            niveau=5
        )

    def test_role_list_view_requires_superuser(self):
        """Test que la liste des rôles nécessite un superuser."""
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('role:list'))
        # Peut être 403 (Forbidden) ou 302 (redirect vers login) selon la config
        self.assertIn(response.status_code, [302, 403])

    def test_role_list_view_superuser(self):
        """Test que la liste des rôles fonctionne pour un superuser."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('role:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Role')

    def test_role_create_view_get(self):
        """Test l'affichage du formulaire de création."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('role:create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Créer un rôle')

    def test_role_create_view_post(self):
        """Test la création d'un rôle."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.post(reverse('role:create'), {
            'nom': 'Nouveau Role',
            'niveau': 10
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Role.objects.filter(nom='Nouveau Role').exists())

    def test_role_update_view(self):
        """Test la modification d'un rôle."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.post(
            reverse('role:update', args=[self.role.pk]),
            {
                'nom': 'Role Modifié',
                'niveau': 5
            }
        )
        self.assertEqual(response.status_code, 302)
        self.role.refresh_from_db()
        self.assertEqual(self.role.nom, 'Role Modifié')

    def test_role_delete_view(self):
        """Test la suppression d'un rôle."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.post(reverse('role:delete', args=[self.role.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Role.objects.filter(pk=self.role.pk).exists())


class UserRoleTest(TestCase):
    """
    Tests pour l'assignation de rôles aux utilisateurs.
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
        self.role = Role.objects.create(
            nom='Test Role',
            niveau=5
        )

    def test_user_role_view_assign_role(self):
        """Test l'assignation d'un rôle à un utilisateur."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.post(
            reverse('role:user_role', args=[self.user.id]),
            {'role': self.role.id}
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, self.role)

    def test_user_role_view_remove_role(self):
        """Test la suppression du rôle d'un utilisateur."""
        self.user.role = self.role
        self.user.save()
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.post(
            reverse('role:user_role', args=[self.user.id]),
            {'role': ''}
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.role)

    def test_user_role_view_change_role(self):
        """Test le changement de rôle d'un utilisateur."""
        role2 = Role.objects.create(
            nom='Autre Role',
            niveau=6
        )
        self.user.role = self.role
        self.user.save()
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.post(
            reverse('role:user_role', args=[self.user.id]),
            {'role': role2.id}
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, role2)


class RolePerformanceTest(TestCase):
    """
    Tests de performance pour les rôles.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        # Créer plusieurs rôles
        for i in range(10):
            Role.objects.create(
                nom=f'Role {i}',
                niveau=i
            )

    def test_role_list_view_optimization(self):
        """Test que la liste des rôles utilise only() pour optimiser."""
        self.client.login(email='admin@example.com', password='adminpass123')
        with self.assertNumQueries(2):  # 1 pour les rôles, 1 pour la pagination
            response = self.client.get(reverse('role:list'))
            self.assertEqual(response.status_code, 200)

    def test_user_list_view_optimization(self):
        """Test que la liste des utilisateurs utilise select_related."""
        self.client.login(email='admin@example.com', password='adminpass123')
        # Créer quelques utilisateurs avec des rôles
        role = Role.objects.first()
        for i in range(5):
            user = User.objects.create_user(
                email=f'user{i}@example.com',
                password='pass123'
            )
            user.role = role
            user.save()
        with self.assertNumQueries(2):  # 1 pour les utilisateurs, 1 pour la pagination
            response = self.client.get(reverse('role:user_list'))
            self.assertEqual(response.status_code, 200)


class RoleSecurityTest(TestCase):
    """
    Tests de sécurité pour les rôles.
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
        self.role = Role.objects.create(
            nom='Test Role',
            niveau=5
        )

    def test_role_views_require_superuser(self):
        """Test que toutes les vues nécessitent un superuser."""
        self.client.login(email='user@example.com', password='userpass123')
        views = [
            'role:list',
            'role:create',
            'role:update',
            'role:delete',
            'role:user_list',
        ]
        for view_name in views:
            if 'update' in view_name or 'delete' in view_name:
                url = reverse(view_name, args=[self.role.pk])
            else:
                url = reverse(view_name)
            response = self.client.get(url)
            # Peut être 403 (Forbidden) ou 302 (redirect vers login) selon la config
            self.assertIn(response.status_code, [302, 403])

    def test_role_delete_preserves_users(self):
        """Test que la suppression d'un rôle préserve les utilisateurs."""
        self.user.role = self.role
        self.user.save()
        self.client.login(email='admin@example.com', password='adminpass123')
        self.client.post(reverse('role:delete', args=[self.role.pk]))
        self.user.refresh_from_db()
        # L'utilisateur existe toujours mais son rôle est null
        self.assertIsNone(self.user.role)
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())
