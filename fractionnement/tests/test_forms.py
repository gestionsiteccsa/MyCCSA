"""
Tests pour les formulaires de l'application fractionnement.
"""
from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from ..forms import CycleHebdomadaireForm, PeriodeCongeForm, ParametresAnneeForm
from ..models import CycleHebdomadaire, PeriodeConge, ParametresAnnee

User = get_user_model()


class CycleHebdomadaireFormTest(TestCase):
    """
    Tests pour le formulaire CycleHebdomadaireForm.
    """
    
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_form_valid_data(self):
        """Test formulaire avec données valides."""
        form = CycleHebdomadaireForm({
            'annee': 2024,
            'heures_semaine': '35',
            'quotite_travail': '1.0',
            'jours_ouvres_ou_ouvrables': 'ouvres',
        }, user=self.user)
        
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_heures_semaine_too_low(self):
        """Test validation heures_semaine < 35."""
        form = CycleHebdomadaireForm({
            'annee': 2024,
            'heures_semaine': '34',
            'quotite_travail': '1.0',
            'jours_ouvres_ou_ouvrables': 'ouvres',
        }, user=self.user)
        
        self.assertFalse(form.is_valid())
        self.assertIn('heures_semaine', form.errors)
    
    def test_form_invalid_heures_semaine_too_high(self):
        """Test validation heures_semaine > 39."""
        form = CycleHebdomadaireForm({
            'annee': 2024,
            'heures_semaine': '40',
            'quotite_travail': '1.0',
            'jours_ouvres_ou_ouvrables': 'ouvres',
        }, user=self.user)
        
        self.assertFalse(form.is_valid())
        self.assertIn('heures_semaine', form.errors)
    
    def test_form_invalid_quotite_too_low(self):
        """Test validation quotite < 0.5."""
        form = CycleHebdomadaireForm({
            'annee': 2024,
            'heures_semaine': '35',
            'quotite_travail': '0.4',
            'jours_ouvres_ou_ouvrables': 'ouvres',
        }, user=self.user)
        
        self.assertFalse(form.is_valid())
        self.assertIn('quotite_travail', form.errors)
    
    def test_form_invalid_quotite_too_high(self):
        """Test validation quotite > 1.0."""
        form = CycleHebdomadaireForm({
            'annee': 2024,
            'heures_semaine': '35',
            'quotite_travail': '1.1',
            'jours_ouvres_ou_ouvrables': 'ouvres',
        }, user=self.user)
        
        self.assertFalse(form.is_valid())
        self.assertIn('quotite_travail', form.errors)
    
    def test_form_duplicate_annee(self):
        """Test qu'on ne peut pas créer deux cycles pour la même année."""
        CycleHebdomadaire.objects.create(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0')
        )
        
        form = CycleHebdomadaireForm({
            'annee': 2024,
            'heures_semaine': '37',
            'quotite_travail': '1.0',
            'jours_ouvres_ou_ouvrables': 'ouvres',
        }, user=self.user)
        
        self.assertFalse(form.is_valid())
        self.assertIn('annee', form.errors)
    
    def test_form_calculates_rtt_automatically(self):
        """Test que le formulaire calcule automatiquement les RTT."""
        form = CycleHebdomadaireForm({
            'annee': 2024,
            'heures_semaine': '39',
            'quotite_travail': '1.0',
            'jours_ouvres_ou_ouvrables': 'ouvres',
        }, user=self.user)
        
        self.assertTrue(form.is_valid())
        cycle = form.save()
        self.assertGreater(cycle.rtt_annuels, 0)
    
    def test_form_calculates_conges_annuels_automatically(self):
        """Test que le formulaire calcule automatiquement les CA."""
        form = CycleHebdomadaireForm({
            'annee': 2024,
            'heures_semaine': '35',
            'quotite_travail': '0.5',
            'jours_ouvres_ou_ouvrables': 'ouvres',
        }, user=self.user)
        
        self.assertTrue(form.is_valid())
        cycle = form.save()
        self.assertEqual(cycle.conges_annuels, Decimal('12.50'))
    
    def test_form_update_existing_cycle(self):
        """Test modification d'un cycle existant."""
        cycle = CycleHebdomadaire.objects.create(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0')
        )
        
        form = CycleHebdomadaireForm({
            'annee': 2024,
            'heures_semaine': '37',
            'quotite_travail': '1.0',
            'jours_ouvres_ou_ouvrables': 'ouvres',
        }, instance=cycle, user=self.user)
        
        self.assertTrue(form.is_valid())
        form.save()
        cycle.refresh_from_db()
        self.assertEqual(cycle.heures_semaine, Decimal('37'))


class PeriodeCongeFormTest(TestCase):
    """
    Tests pour le formulaire PeriodeCongeForm.
    """
    
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_form_valid_data(self):
        """Test formulaire avec données valides."""
        form = PeriodeCongeForm({
            'date_debut': '2024-07-01',
            'date_fin': '2024-07-15',
            'type_conge': 'annuel',
        }, user=self.user)
        
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_date_fin_before_date_debut(self):
        """Test validation date_fin < date_debut."""
        form = PeriodeCongeForm({
            'date_debut': '2024-07-15',
            'date_fin': '2024-07-01',
            'type_conge': 'annuel',
        }, user=self.user)
        
        self.assertFalse(form.is_valid())
        self.assertIn('date_fin', form.errors)
    
    def test_form_calculates_annee_civile_automatically(self):
        """Test que le formulaire calcule automatiquement l'année civile."""
        form = PeriodeCongeForm({
            'date_debut': '2024-07-01',
            'date_fin': '2024-07-15',
            'type_conge': 'annuel',
        }, user=self.user)
        
        self.assertTrue(form.is_valid())
        periode = form.save()
        self.assertEqual(periode.annee_civile, 2024)
    
    def test_form_calculates_nb_jours_automatically(self):
        """Test que le formulaire calcule automatiquement le nombre de jours."""
        form = PeriodeCongeForm({
            'date_debut': '2024-07-01',
            'date_fin': '2024-07-15',
            'type_conge': 'annuel',
        }, user=self.user)
        
        self.assertTrue(form.is_valid())
        periode = form.save()
        self.assertGreater(periode.nb_jours, 0)
    
    def test_form_uses_parametres_annee_for_calculation(self):
        """Test que le formulaire utilise les paramètres de l'année pour le calcul."""
        ParametresAnnee.objects.create(
            user=self.user,
            annee=2024,
            jours_ouvres_ou_ouvrables='ouvrables'
        )
        
        form = PeriodeCongeForm({
            'date_debut': '2024-07-01',
            'date_fin': '2024-07-15',
            'type_conge': 'annuel',
        }, user=self.user)
        
        self.assertTrue(form.is_valid())
        periode = form.save()
        # Le nombre de jours devrait être calculé avec jours ouvrables
        self.assertGreater(periode.nb_jours, 0)
    
    def test_form_uses_cycle_for_calculation_if_no_parametres(self):
        """Test que le formulaire utilise le cycle si pas de paramètres."""
        CycleHebdomadaire.objects.create(
            user=self.user,
            annee=2024,
            heures_semaine=Decimal('35'),
            quotite_travail=Decimal('1.0'),
            jours_ouvres_ou_ouvrables='ouvrables'
        )
        
        form = PeriodeCongeForm({
            'date_debut': '2024-07-01',
            'date_fin': '2024-07-15',
            'type_conge': 'annuel',
        }, user=self.user)
        
        self.assertTrue(form.is_valid())
        periode = form.save()
        self.assertGreater(periode.nb_jours, 0)


class ParametresAnneeFormTest(TestCase):
    """
    Tests pour le formulaire ParametresAnneeForm.
    """
    
    def setUp(self):
        """Configuration initiale."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_form_valid_data(self):
        """Test formulaire avec données valides."""
        form = ParametresAnneeForm({
            'annee': 2024,
            'jours_ouvres_ou_ouvrables': 'ouvres',
        }, user=self.user)
        
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_annee_too_low(self):
        """Test validation annee < 2020."""
        form = ParametresAnneeForm({
            'annee': 2019,
            'jours_ouvres_ou_ouvrables': 'ouvres',
        }, user=self.user)
        
        self.assertFalse(form.is_valid())
        self.assertIn('annee', form.errors)
    
    def test_form_invalid_annee_too_high(self):
        """Test validation annee > 2100."""
        form = ParametresAnneeForm({
            'annee': 2101,
            'jours_ouvres_ou_ouvrables': 'ouvres',
        }, user=self.user)
        
        self.assertFalse(form.is_valid())
        self.assertIn('annee', form.errors)
    
    def test_form_duplicate_annee(self):
        """Test qu'on ne peut pas créer deux paramètres pour la même année."""
        ParametresAnnee.objects.create(
            user=self.user,
            annee=2024,
            jours_ouvres_ou_ouvrables='ouvres'
        )
        
        form = ParametresAnneeForm({
            'annee': 2024,
            'jours_ouvres_ou_ouvrables': 'ouvrables',
        }, user=self.user)
        
        self.assertFalse(form.is_valid())
        self.assertIn('annee', form.errors)
    
    def test_form_update_existing_parametres(self):
        """Test modification de paramètres existants."""
        parametres = ParametresAnnee.objects.create(
            user=self.user,
            annee=2024,
            jours_ouvres_ou_ouvrables='ouvres'
        )
        
        form = ParametresAnneeForm({
            'annee': 2024,
            'jours_ouvres_ou_ouvrables': 'ouvrables',
        }, instance=parametres, user=self.user)
        
        self.assertTrue(form.is_valid())
        form.save()
        parametres.refresh_from_db()
        self.assertEqual(parametres.jours_ouvres_ou_ouvrables, 'ouvrables')

