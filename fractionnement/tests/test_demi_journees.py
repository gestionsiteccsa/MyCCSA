"""
Tests pour la gestion des demi-journées de congé.
"""
from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import PeriodeConge, CycleHebdomadaire, ParametresAnnee
from ..services.calcul_service import compter_jours_periode, get_jours_hors_periode_principale

User = get_user_model()

class DemiJourneesTest(TestCase):
    """
    Tests pour vérifier le calcul des demi-journées.
    """

    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            email='demi_test@example.com',
            password='testpass123'
        )
        # Cycle standard 35h, jours ouvrés
        CycleHebdomadaire.objects.create(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0'),
            jours_ouvres_ou_ouvrables='ouvres'
        )
        ParametresAnnee.objects.create(
            user=self.user,
            annee=2024,
            jours_ouvres_ou_ouvrables='ouvres'
        )

    def test_compter_jours_periode_matin_matin(self):
        """Test: Lundi Matin au Lundi Matin = 0.5 jour."""
        # Lundi 1er Juillet 2024
        d = date(2024, 7, 1)
        nb_jours = compter_jours_periode(
            d, d, 'ouvres', True, 2024,
            debut_type='matin', fin_type='matin'
        )
        self.assertEqual(nb_jours, Decimal('0.5'))

    def test_compter_jours_periode_apres_midi_apres_midi(self):
        """Test: Lundi Après-midi au Lundi Après-midi = 0.5 jour."""
        d = date(2024, 7, 1)
        nb_jours = compter_jours_periode(
            d, d, 'ouvres', True, 2024,
            debut_type='apres_midi', fin_type='apres_midi'
        )
        self.assertEqual(nb_jours, Decimal('0.5'))

    def test_compter_jours_periode_matin_apres_midi(self):
        """Test: Lundi Matin au Lundi Après-midi = 1 jour."""
        d = date(2024, 7, 1)
        nb_jours = compter_jours_periode(
            d, d, 'ouvres', True, 2024,
            debut_type='matin', fin_type='apres_midi'
        )
        self.assertEqual(nb_jours, Decimal('1.0'))

    def test_compter_jours_periode_apres_midi_matin_lendemain(self):
        """Test: Lundi Après-midi au Mardi Matin = 1 jour."""
        d1 = date(2024, 7, 1) # Lundi
        d2 = date(2024, 7, 2) # Mardi
        nb_jours = compter_jours_periode(
            d1, d2, 'ouvres', True, 2024,
            debut_type='apres_midi', fin_type='matin'
        )
        self.assertEqual(nb_jours, Decimal('1.0'))

    def test_compter_jours_periode_apres_midi_apres_midi_lendemain(self):
        """Test: Lundi Après-midi au Mardi Après-midi = 1.5 jours."""
        d1 = date(2024, 7, 1) # Lundi
        d2 = date(2024, 7, 2) # Mardi
        nb_jours = compter_jours_periode(
            d1, d2, 'ouvres', True, 2024,
            debut_type='apres_midi', fin_type='apres_midi'
        )
        self.assertEqual(nb_jours, Decimal('1.5'))

    def test_calcul_fractionnement_demi_journees(self):
        """Test que les demi-journées sont prises en compte pour le fractionnement."""
        # Créer 4.5 jours hors période (ne devrait pas donner de fractionnement car < 5)
        # Lundi 4 nov (Matin) au Vendredi 8 nov (Matin) = 4.5 jours
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 11, 4),
            debut_type='matin',
            date_fin=date(2024, 11, 8),
            fin_type='matin',
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=Decimal('4.5')
        )
        
        jours_hors = get_jours_hors_periode_principale(self.user, 2024)
        # get_jours_hors_periode_principale retourne int (partie entière)
        self.assertEqual(jours_hors, 4)
        
        # Ajouter 0.5 jour pour arriver à 5 jours
        # Vendredi 8 nov (Après-midi) au Vendredi 8 nov (Après-midi) = 0.5 jour
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 11, 8),
            debut_type='apres_midi',
            date_fin=date(2024, 11, 8),
            fin_type='apres_midi',
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=Decimal('0.5')
        )
        
        jours_hors = get_jours_hors_periode_principale(self.user, 2024)
        self.assertEqual(jours_hors, 5)
