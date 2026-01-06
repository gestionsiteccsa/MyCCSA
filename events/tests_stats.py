from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from events.models import Event
from role.models import Role

User = get_user_model()

class EventStatsPermissionTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # 1. Superuser
        self.superuser = User.objects.create_superuser(
            email='admin@test.com',
            password='password123',
            first_name='Admin',
            last_name='User'
        )
        
        # 2. Chargé de communication (Use specific niveau to avoid clash if 0/1 specific usage exists)
        self.role_com, _ = Role.objects.get_or_create(
            nom='Chargé de communication', 
            defaults={'niveau': 98}
        )
        self.user_com = User.objects.create_user(
            email='com@test.com',
            password='password123',
            first_name='Com',
            last_name='User'
        )
        self.user_com.role = self.role_com
        self.user_com.save()
        
        # 3. Standard User (Agent)
        self.role_agent, _ = Role.objects.get_or_create(
            nom='Agent', 
            defaults={'niveau': 99}
        )
        self.user_agent = User.objects.create_user(
            email='agent@test.com',
            password='password123',
            first_name='Agent',
            last_name='User'
        )
        self.user_agent.role = self.role_agent
        self.user_agent.save()
        
        self.url = reverse('events:stats')

    def test_superuser_access(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
    
    def test_charge_com_access(self):
        self.client.force_login(self.user_com)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_agent_access_denied(self):
        self.client.force_login(self.user_agent)
        response = self.client.get(self.url)
        # user_passes_test redirects to login by default if failed, or raises 302
        self.assertEqual(response.status_code, 302) 
        # Check it redirects to login page (default Django behavior for @user_passes_test)
        self.assertTrue('/accounts/login/' in response.url)

