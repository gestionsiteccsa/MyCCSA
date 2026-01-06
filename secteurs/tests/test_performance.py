"""
Tests de performance pour l'application secteurs.
"""
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.db import connection, reset_queries
from django.urls import reverse
from secteurs.models import Secteur
import time

User = get_user_model()


class PerformanceTest(TestCase):
    """
    Tests de performance pour les vues.
    """
    def setUp(self):
        """Configuration initiale."""
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.client.login(email='admin@example.com', password='adminpass123')

    def test_list_view_performance_with_many_secteurs(self):
        """Test les performances avec 100+ secteurs."""
        # Créer 100 secteurs
        for i in range(100):
            Secteur.objects.create(
                nom=f'Secteur {i}',
                couleur='#000000',
                ordre=i
            )
        
        reset_queries()
        start_time = time.time()
        
        response = self.client.get(reverse('secteurs:list'))
        
        elapsed_time = time.time() - start_time
        query_count = len(connection.queries)
        
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que le temps de réponse est raisonnable (< 1 seconde)
        self.assertLess(elapsed_time, 1.0, 
                       f"Temps de réponse trop long: {elapsed_time:.3f}s")
        
        # Vérifier que le nombre de requêtes est raisonnable (< 10)
        self.assertLess(query_count, 10,
                       f"Trop de requêtes SQL: {query_count}")

    def test_query_count_optimization(self):
        """Test que l'optimisation avec only() réduit le nombre de requêtes."""
        # Créer des secteurs
        for i in range(50):
            Secteur.objects.create(
                nom=f'Secteur {i}',
                couleur='#000000',
                ordre=i
            )
        
        # Test avec l'optimisation (only)
        reset_queries()
        response = self.client.get(reverse('secteurs:list'))
        queries_optimized = len(connection.queries)
        
        self.assertEqual(response.status_code, 200)
        
        # Le nombre de requêtes devrait être faible
        # (1 pour la session, 1 pour l'utilisateur, 1 pour les secteurs)
        self.assertLessEqual(queries_optimized, 8,
                           f"Trop de requêtes même avec optimisation: {queries_optimized}")

    def test_list_view_scalability(self):
        """Test la scalabilité de la vue avec différents nombres de secteurs."""
        test_sizes = [10, 50, 100]
        query_counts = []
        response_times = []
        
        for size in test_sizes:
            # Nettoyer les secteurs précédents
            Secteur.objects.all().delete()
            
            # Créer le nombre de secteurs spécifié
            for i in range(size):
                Secteur.objects.create(
                    nom=f'Secteur {i}',
                    couleur='#000000',
                    ordre=i
                )
            
            reset_queries()
            start_time = time.time()
            
            response = self.client.get(reverse('secteurs:list'))
            
            elapsed_time = time.time() - start_time
            query_count = len(connection.queries)
            
            query_counts.append(query_count)
            response_times.append(elapsed_time)
            
            self.assertEqual(response.status_code, 200)
        
        # Vérifier que le nombre de requêtes ne croît pas linéairement
        # (pas de N+1 query)
        if len(query_counts) >= 2:
            # La différence entre 10 et 100 secteurs ne devrait pas être énorme
            diff = query_counts[-1] - query_counts[0]
            self.assertLess(diff, 5,
                          f"Le nombre de requêtes croît trop: {query_counts[0]} -> {query_counts[-1]}")
        
        # Vérifier que le temps de réponse reste raisonnable
        max_time = max(response_times)
        self.assertLess(max_time, 1.0,
                       f"Temps de réponse trop long avec {test_sizes[-1]} secteurs: {max_time:.3f}s")

    def test_pagination_performance(self):
        """Test que la pagination améliore les performances."""
        # Créer 100 secteurs
        for i in range(100):
            Secteur.objects.create(
                nom=f'Secteur {i}',
                couleur='#000000',
                ordre=i
            )
        
        # Test première page
        reset_queries()
        response1 = self.client.get(reverse('secteurs:list'))
        queries_page1 = len(connection.queries)
        
        # Test deuxième page
        reset_queries()
        response2 = self.client.get(reverse('secteurs:list') + '?page=2')
        queries_page2 = len(connection.queries)
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Les deux pages devraient avoir un nombre similaire de requêtes
        # (la pagination limite le nombre d'objets chargés)
        self.assertLessEqual(abs(queries_page1 - queries_page2), 2,
                            f"Différence trop grande entre les pages: {queries_page1} vs {queries_page2}")












