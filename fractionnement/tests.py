"""
Tests de l'application fractionnement.
"""
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import CycleHebdomadaire, PeriodeConge, ParametresAnnee, CalculFractionnement
from .services.calcul_service import (
    calculer_rtt_annuels,
    calculer_conges_annuels,
    calculer_jours_fractionnement,
    compter_jours_periode,
    get_jours_hors_periode_principale,
    calculer_fractionnement_complet,
)
from .services.calendrier_service import (
    get_calendrier_data,
    get_jours_feries_list,
    get_vacances_zone_b_list,
    get_periodes_conges_user,
)
from .utils import (
    get_jours_feries,
    est_jour_ouvre,
    est_jour_ouvrable,
    est_dans_periode_principale,
    compter_jours_ouvres,
    compter_jours_ouvrables,
)

User = get_user_model()


class CalculServiceTest(TestCase):
    """
    Tests pour le service de calcul.
    """
    
    def test_calculer_rtt_annuels_35h(self):
        """Test calcul RTT pour 35h/semaine."""
        rtt = calculer_rtt_annuels(Decimal('35'), Decimal('1.0'))
        self.assertEqual(rtt, 0)
    
    def test_calculer_rtt_annuels_39h(self):
        """Test calcul RTT pour 39h/semaine."""
        rtt = calculer_rtt_annuels(Decimal('39'), Decimal('1.0'))
        # (39 * 52 - 1607) / 39 = (2028 - 1607) / 39 = 421 / 39 ≈ 10.79 → 11
        self.assertGreater(rtt, 0)
    
    def test_calculer_rtt_annuels_mi_temps(self):
        """Test calcul RTT pour mi-temps."""
        rtt_plein = calculer_rtt_annuels(Decimal('39'), Decimal('1.0'))
        rtt_mi_temps = calculer_rtt_annuels(Decimal('39'), Decimal('0.5'))
        self.assertLess(rtt_mi_temps, rtt_plein)
    
    def test_calculer_conges_annuels_plein_temps(self):
        """Test calcul CA pour temps complet."""
        ca = calculer_conges_annuels(Decimal('1.0'))
        self.assertEqual(ca, Decimal('25.00'))
    
    def test_calculer_conges_annuels_mi_temps(self):
        """Test calcul CA pour mi-temps."""
        ca = calculer_conges_annuels(Decimal('0.5'))
        self.assertEqual(ca, Decimal('12.50'))
    
    def test_calculer_jours_fractionnement_0(self):
        """Test calcul fractionnement avec moins de 3 jours."""
        jours = calculer_jours_fractionnement(2)
        self.assertEqual(jours, 0)
    
    def test_calculer_jours_fractionnement_1(self):
        """Test calcul fractionnement avec 3-5 jours."""
        jours = calculer_jours_fractionnement(4)
        self.assertEqual(jours, 1)
    
    def test_calculer_jours_fractionnement_2(self):
        """Test calcul fractionnement avec 6 jours et plus."""
        jours = calculer_jours_fractionnement(6)
        self.assertEqual(jours, 2)
        jours = calculer_jours_fractionnement(10)
        self.assertEqual(jours, 2)


class UtilsTest(TestCase):
    """
    Tests pour les utilitaires.
    """
    
    def test_get_jours_feries(self):
        """Test récupération des jours fériés."""
        jours_feries = get_jours_feries(2024)
        self.assertGreater(len(jours_feries), 0)
        # Vérifier que le 1er janvier est présent
        self.assertIn(date(2024, 1, 1), jours_feries)
    
    def test_est_jour_ouvre(self):
        """Test vérification jour ouvré."""
        # Lundi = jour ouvré
        self.assertTrue(est_jour_ouvre(date(2024, 1, 1)))  # Lundi
        # Dimanche = pas jour ouvré
        self.assertFalse(est_jour_ouvre(date(2024, 1, 7)))  # Dimanche
    
    def test_est_jour_ouvrable(self):
        """Test vérification jour ouvrable."""
        # Samedi = jour ouvrable
        self.assertTrue(est_jour_ouvrable(date(2024, 1, 6)))  # Samedi
        # Dimanche = pas jour ouvrable
        self.assertFalse(est_jour_ouvrable(date(2024, 1, 7)))  # Dimanche
    
    def test_est_dans_periode_principale(self):
        """Test vérification période principale."""
        # 15 juillet = dans période principale
        self.assertTrue(est_dans_periode_principale(date(2024, 7, 15)))
        # 15 décembre = hors période principale
        self.assertFalse(est_dans_periode_principale(date(2024, 12, 15)))


class CycleHebdomadaireModelTest(TestCase):
    """
    Tests pour le modèle CycleHebdomadaire.
    """
    
    def setUp(self):
        """Créer un utilisateur de test."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_cycle(self):
        """Test création d'un cycle."""
        cycle = CycleHebdomadaire.objects.create(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0'),
            jours_ouvres_ou_ouvrables='ouvres'
        )
        self.assertEqual(cycle.annee, 2024)
        self.assertEqual(cycle.heures_semaine, Decimal('35'))
    
    def test_unique_together(self):
        """Test unicité user + annee."""
        CycleHebdomadaire.objects.create(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0')
        )
        # Ne doit pas pouvoir créer un deuxième cycle pour la même année
        with self.assertRaises(Exception):
            CycleHebdomadaire.objects.create(
                user=self.user,
                annee=2024,
                heures_semaine=Decimal('37'),
                quotite_travail=Decimal('1.0')
            )
    
    def test_cycle_clean_heures_semaine_too_low(self):
        """Test validation clean() avec heures_semaine < 35."""
        cycle = CycleHebdomadaire(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('34'),
            quotite_travail=Decimal('1.0')
        )
        
        with self.assertRaises(ValidationError):
            cycle.clean()
    
    def test_cycle_clean_heures_semaine_too_high(self):
        """Test validation clean() avec heures_semaine > 39."""
        cycle = CycleHebdomadaire(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('40'),
            quotite_travail=Decimal('1.0')
        )
        
        with self.assertRaises(ValidationError):
            cycle.clean()
    
    def test_cycle_clean_valid_heures(self):
        """Test validation clean() avec heures valides."""
        cycle = CycleHebdomadaire(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0')
        )
        
        # Ne doit pas lever d'exception
        try:
            cycle.clean()
        except ValidationError:
            self.fail("clean() a levé une ValidationError pour des heures valides")
    
    def test_cycle_str(self):
        """Test méthode __str__."""
        cycle = CycleHebdomadaire.objects.create(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0')
        )
        
        str_repr = str(cycle)
        self.assertIn('2024', str_repr)
        self.assertIn('35', str_repr)


class PeriodeCongeModelTest(TestCase):
    """
    Tests pour le modèle PeriodeConge.
    """
    
    def setUp(self):
        """Créer un utilisateur de test."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_periode(self):
        """Test création d'une période."""
        periode = PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 7, 1),
            date_fin=date(2024, 7, 15),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=10
        )
        self.assertEqual(periode.type_conge, 'annuel')
        self.assertEqual(periode.annee_civile, 2024)
    
    def test_periode_clean_date_fin_before_date_debut(self):
        """Test validation clean() avec date_fin < date_debut."""
        periode = PeriodeConge(
            user=self.user,
            date_debut=date(2024, 7, 15),
            date_fin=date(2024, 7, 1),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=10
        )
        
        with self.assertRaises(ValidationError):
            periode.clean()
    
    def test_periode_clean_valid_dates(self):
        """Test validation clean() avec dates valides."""
        periode = PeriodeConge(
            user=self.user,
            date_debut=date(2024, 7, 1),
            date_fin=date(2024, 7, 15),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=10
        )
        
        # Ne doit pas lever d'exception
        try:
            periode.clean()
        except ValidationError:
            self.fail("clean() a levé une ValidationError pour des dates valides")
    
    def test_periode_str(self):
        """Test méthode __str__."""
        periode = PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 7, 1),
            date_fin=date(2024, 7, 15),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=10
        )
        
        str_repr = str(periode)
        self.assertIn('2024-07-01', str_repr)
        self.assertIn('2024-07-15', str_repr)
        self.assertIn('annuel', str_repr)


class FractionnementIntegrationTest(TestCase):
    """
    Tests d'intégration pour le calcul de fractionnement.
    """
    
    def setUp(self):
        """Créer un utilisateur et des données de test."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Créer un cycle
        self.cycle = CycleHebdomadaire.objects.create(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0'),
            jours_ouvres_ou_ouvrables='ouvres',
            rtt_annuels=0,
            conges_annuels=Decimal('25.00')
        )
        
        # Créer des paramètres
        self.parametres = ParametresAnnee.objects.create(
            user=self.user,
            annee=2024,
            jours_ouvres_ou_ouvrables='ouvres'
        )
    
    def test_calcul_fractionnement_complet(self):
        """Test calcul complet du fractionnement."""
        # Créer une période de congés hors période principale (décembre)
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 12, 1),
            date_fin=date(2024, 12, 6),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=4
        )
        
        # Calculer le fractionnement
        jours_hors = get_jours_hors_periode_principale(self.user, 2024)
        jours_fractionnement = calculer_jours_fractionnement(jours_hors)
        
        # 4 jours hors période → 1 jour de fractionnement
        self.assertGreaterEqual(jours_hors, 3)
        self.assertEqual(jours_fractionnement, 1)
    
    def test_calcul_fractionnement_complet_with_multiple_periodes(self):
        """Test calcul avec plusieurs périodes."""
        # Période dans période principale (ne compte pas)
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 7, 1),
            date_fin=date(2024, 7, 10),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=7
        )
        
        # Période hors période principale (compte)
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 12, 1),
            date_fin=date(2024, 12, 10),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=7
        )
        
        calcul = calculer_fractionnement_complet(self.user, 2024)
        
        self.assertIn('jours_hors_periode', calcul)
        self.assertIn('jours_fractionnement', calcul)
        self.assertIn('annee', calcul)
        self.assertEqual(calcul['annee'], 2024)
        self.assertGreaterEqual(calcul['jours_hors_periode'], 3)
    
    def test_calcul_fractionnement_complet_no_periodes(self):
        """Test calcul sans périodes."""
        calcul = calculer_fractionnement_complet(self.user, 2024)
        
        self.assertEqual(calcul['jours_hors_periode'], 0)
        self.assertEqual(calcul['jours_fractionnement'], 0)
        self.assertEqual(calcul['annee'], 2024)


class CalendrierServiceTest(TestCase):
    """
    Tests pour le service de calendrier.
    """
    
    def setUp(self):
        """Créer un utilisateur et des données de test."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_get_jours_feries_list(self):
        """Test récupération de la liste des jours fériés formatés."""
        jours_feries = get_jours_feries_list(2024)
        
        self.assertIsInstance(jours_feries, list)
        self.assertGreater(len(jours_feries), 0)
        
        # Vérifier la structure
        for jour_ferie in jours_feries:
            self.assertIn('date', jour_ferie)
            self.assertIn('nom', jour_ferie)
            self.assertIn('type', jour_ferie)
            self.assertEqual(jour_ferie['type'], 'ferie')
    
    def test_get_vacances_zone_b_list(self):
        """Test récupération de la liste des vacances Zone B formatées."""
        vacances = get_vacances_zone_b_list(2024)
        
        self.assertIsInstance(vacances, list)
        self.assertGreater(len(vacances), 0)
        
        # Vérifier la structure
        for vacance in vacances:
            self.assertIn('date_debut', vacance)
            self.assertIn('date_fin', vacance)
            self.assertIn('nom', vacance)
            self.assertIn('type', vacance)
            self.assertEqual(vacance['type'], 'vacance')
    
    def test_get_periodes_conges_user(self):
        """Test récupération des périodes de congés d'un utilisateur."""
        # Créer quelques périodes
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 7, 1),
            date_fin=date(2024, 7, 15),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=10
        )
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 12, 1),
            date_fin=date(2024, 12, 6),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=4
        )
        
        periodes = get_periodes_conges_user(self.user, 2024)
        
        self.assertIsInstance(periodes, list)
        self.assertEqual(len(periodes), 2)
        
        # Vérifier la structure
        for periode in periodes:
            self.assertIn('id', periode)
            self.assertIn('date_debut', periode)
            self.assertIn('date_fin', periode)
            self.assertIn('type_conge', periode)
            self.assertIn('nb_jours', periode)
            self.assertIn('dans_periode_principale', periode)
            self.assertIn('type', periode)
            self.assertEqual(periode['type'], 'conge')
    
    def test_get_periodes_conges_user_empty(self):
        """Test récupération des périodes quand il n'y en a pas."""
        periodes = get_periodes_conges_user(self.user, 2024)
        self.assertEqual(len(periodes), 0)
    
    def test_get_periodes_conges_user_other_year(self):
        """Test que seules les périodes de l'année demandée sont retournées."""
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2023, 7, 1),
            date_fin=date(2023, 7, 15),
            type_conge='annuel',
            annee_civile=2023,
            nb_jours=10
        )
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 7, 1),
            date_fin=date(2024, 7, 15),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=10
        )
        
        periodes = get_periodes_conges_user(self.user, 2024)
        self.assertEqual(len(periodes), 1)
        self.assertIn('2024-07-01', periodes[0]['date_debut'])
    
    def test_get_calendrier_data(self):
        """Test récupération de toutes les données du calendrier."""
        # Créer une période
        PeriodeConge.objects.create(
            user=self.user,
            date_debut=date(2024, 7, 1),
            date_fin=date(2024, 7, 15),
            type_conge='annuel',
            annee_civile=2024,
            nb_jours=10
        )
        
        data = get_calendrier_data(self.user, 2024)
        
        self.assertIn('annee', data)
        self.assertIn('jours_feries', data)
        self.assertIn('vacances_zone_b', data)
        self.assertIn('periodes_conges', data)
        
        self.assertEqual(data['annee'], 2024)
        self.assertIsInstance(data['jours_feries'], list)
        self.assertIsInstance(data['vacances_zone_b'], list)
        self.assertIsInstance(data['periodes_conges'], list)
        self.assertEqual(len(data['periodes_conges']), 1)
