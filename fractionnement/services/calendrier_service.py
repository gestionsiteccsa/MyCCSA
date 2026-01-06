"""
Service de gestion du calendrier pour l'application fractionnement.
"""
from datetime import date
from typing import List, Dict, Any
from django.contrib.auth import get_user_model

from ..models import PeriodeConge
from ..utils import (
    get_jours_feries,
    get_vacances_zone_b,
    est_dans_periode_principale,
)

User = get_user_model()


def get_jours_feries_list(annee: int) -> List[Dict[str, Any]]:
    """
    Retourne la liste des jours fériés formatés pour le calendrier.

    Args:
        annee: Année civile

    Returns:
        List[Dict[str, Any]]: Liste des jours fériés avec date et nom
    """
    jours_feries = get_jours_feries(annee)
    
    # Noms des jours fériés
    noms_feries = {
        1: "Jour de l'an",
        5: "Fête du Travail",
        8: "Victoire en Europe",
        14: "Fête nationale",
        15: "Assomption",
        11: "Toussaint",
        25: "Noël",
    }
    
    result = []
    for jour_ferie in jours_feries:
        nom = noms_feries.get(jour_ferie.day, "Jour férié")
        # Pour les jours fériés variables, déterminer le nom
        if jour_ferie.month == 3 or jour_ferie.month == 4:
            # Pâques ou lundi de Pâques
            if jour_ferie.weekday() == 0:  # Lundi
                nom = "Lundi de Pâques"
            else:
                nom = "Pâques"
        elif jour_ferie.month == 5 and jour_ferie.day > 15:
            nom = "Ascension"
        elif jour_ferie.month == 5 and jour_ferie.day > 20:
            nom = "Lundi de Pentecôte"
        
        result.append({
            'date': jour_ferie.isoformat(),
            'nom': nom,
            'type': 'ferie',
        })
    
    return result


def get_vacances_zone_b_list(annee: int) -> List[Dict[str, Any]]:
    """
    Retourne la liste des vacances zone B formatées pour le calendrier.

    Args:
        annee: Année civile

    Returns:
        List[Dict[str, Any]]: Liste des périodes de vacances
    """
    vacances = get_vacances_zone_b(annee)
    
    result = []
    for date_debut, date_fin, nom in vacances:
        result.append({
            'date_debut': date_debut.isoformat(),
            'date_fin': date_fin.isoformat(),
            'nom': nom,
            'type': 'vacance',
        })
    
    return result


def get_periodes_conges_user(user: User, annee: int) -> List[Dict[str, Any]]:
    """
    Retourne les périodes de congés d'un utilisateur formatées pour le calendrier.

    Args:
        user: Utilisateur concerné
        annee: Année civile

    Returns:
        List[Dict[str, Any]]: Liste des périodes de congés
    """
    # Utiliser values() pour optimiser la requête (évite de charger les objets complets)
    periodes = PeriodeConge.objects.filter(
        user=user,
        annee_civile=annee
    ).values(
        'id', 'date_debut', 'date_fin', 'type_conge', 'nb_jours'
    ).order_by('date_debut')
    
    result = []
    for periode in periodes:
        # Déterminer si la période est dans la période principale
        dans_periode_principale = est_dans_periode_principale(periode['date_debut'])
        
        result.append({
            'id': periode['id'],
            'date_debut': periode['date_debut'].isoformat(),
            'date_fin': periode['date_fin'].isoformat(),
            'type_conge': periode['type_conge'],
            'nb_jours': periode['nb_jours'],
            'dans_periode_principale': dans_periode_principale,
            'type': 'conge',
        })
    
    return result


def get_calendrier_data(user: User, annee: int) -> Dict[str, Any]:
    """
    Retourne toutes les données du calendrier pour un utilisateur et une année.

    Args:
        user: Utilisateur concerné
        annee: Année civile

    Returns:
        Dict[str, Any]: Dictionnaire avec toutes les données du calendrier
    """
    return {
        'annee': annee,
        'jours_feries': get_jours_feries_list(annee),
        'vacances_zone_b': get_vacances_zone_b_list(annee),
        'periodes_conges': get_periodes_conges_user(user, annee),
    }





