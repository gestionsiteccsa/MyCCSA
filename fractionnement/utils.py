"""
Utilitaires pour l'application fractionnement.
"""
from datetime import date, timedelta
from typing import List, Tuple, Dict
import calendar
from django.core.cache import cache

# Import des constantes pour éviter les imports circulaires
CACHE_DURATION_ONE_YEAR = 31536000  # 1 an en secondes


def get_jours_feries_fixes(annee: int) -> List[date]:
    """
    Retourne la liste des jours fériés fixes pour une année donnée.

    Args:
        annee: Année civile

    Returns:
        List[date]: Liste des jours fériés fixes
    """
    return [
        date(annee, 1, 1),    # Jour de l'an
        date(annee, 5, 1),    # Fête du Travail
        date(annee, 5, 8),    # Victoire en Europe
        date(annee, 7, 14),   # Fête nationale
        date(annee, 8, 15),   # Assomption
        date(annee, 11, 1),   # Toussaint
        date(annee, 11, 11),  # Armistice
        date(annee, 12, 25),  # Noël
    ]


def calculer_paques(annee: int) -> date:
    """
    Calcule la date de Pâques pour une année donnée (algorithme de Gauss).

    Args:
        annee: Année civile

    Returns:
        date: Date de Pâques
    """
    # Algorithme de Gauss pour calculer Pâques
    a = annee % 19
    b = annee // 100
    c = annee % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mois = (h + l - 7 * m + 114) // 31
    jour = ((h + l - 7 * m + 114) % 31) + 1
    
    return date(annee, mois, jour)


def get_jours_feries_variables(annee: int) -> List[date]:
    """
    Retourne la liste des jours fériés variables (basés sur Pâques).

    Args:
        annee: Année civile

    Returns:
        List[date]: Liste des jours fériés variables
    """
    paques = calculer_paques(annee)
    
    return [
        paques - timedelta(days=2),  # Vendredi saint (non férié en France métropolitaine, mais inclus pour référence)
        paques,                       # Pâques
        paques + timedelta(days=1),   # Lundi de Pâques
        paques + timedelta(days=39),  # Ascension (40 jours après Pâques)
        paques + timedelta(days=50),  # Lundi de Pentecôte
    ]


def get_jours_feries(annee: int) -> List[date]:
    """
    Retourne la liste complète des jours fériés pour une année donnée.
    
    Utilise le cache pour éviter de recalculer les jours fériés à chaque appel.

    Args:
        annee: Année civile

    Returns:
        List[date]: Liste de tous les jours fériés
    """
    cache_key = f'jours_feries_{annee}'
    jours_feries = cache.get(cache_key)
    
    if jours_feries is None:
        jours_feries = get_jours_feries_fixes(annee)
        # Ajouter les jours fériés variables (sauf vendredi saint qui n'est pas férié en France métropolitaine)
        paques = calculer_paques(annee)
        jours_feries.extend([
            paques,                       # Pâques
            paques + timedelta(days=1),   # Lundi de Pâques
            paques + timedelta(days=39), # Ascension
            paques + timedelta(days=50), # Lundi de Pentecôte
        ])
        jours_feries = sorted(jours_feries)
        # Mettre en cache pour 1 an
        cache.set(cache_key, jours_feries, CACHE_DURATION_ONE_YEAR)
    
    return jours_feries


def est_jour_ouvre(d: date) -> bool:
    """
    Vérifie si une date est un jour ouvré (lundi à vendredi).

    Args:
        d: Date à vérifier

    Returns:
        bool: True si jour ouvré, False sinon
    """
    # 0 = lundi, 6 = dimanche
    return d.weekday() < 5


def est_jour_ouvrable(d: date) -> bool:
    """
    Vérifie si une date est un jour ouvrable (lundi à samedi).

    Args:
        d: Date à vérifier

    Returns:
        bool: True si jour ouvrable, False sinon
    """
    # 0 = lundi, 6 = dimanche
    return d.weekday() < 6


def compter_jours_ouvres(date_debut: date, date_fin: date, exclure_feries: bool = True, annee: int = None) -> int:
    """
    Compte le nombre de jours ouvrés entre deux dates.

    Args:
        date_debut: Date de début
        date_fin: Date de fin (incluse)
        exclure_feries: Si True, exclut les jours fériés
        annee: Année pour calculer les jours fériés (si None, utilise année de date_debut)

    Returns:
        int: Nombre de jours orvrés
    """
    if annee is None:
        annee = date_debut.year
    
    jours_feries = set(get_jours_feries(annee)) if exclure_feries else set()
    
    compteur = 0
    current = date_debut
    
    while current <= date_fin:
        if est_jour_ouvre(current) and current not in jours_feries:
            compteur += 1
        current += timedelta(days=1)
    
    return compteur


def compter_jours_ouvrables(date_debut: date, date_fin: date, exclure_feries: bool = True, annee: int = None) -> int:
    """
    Compte le nombre de jours ouvrables entre deux dates.

    Args:
        date_debut: Date de début
        date_fin: Date de fin (incluse)
        exclure_feries: Si True, exclut les jours fériés
        annee: Année pour calculer les jours fériés (si None, utilise année de date_debut)

    Returns:
        int: Nombre de jours ouvrables
    """
    if annee is None:
        annee = date_debut.year
    
    jours_feries = set(get_jours_feries(annee)) if exclure_feries else set()
    
    compteur = 0
    current = date_debut
    
    while current <= date_fin:
        if est_jour_ouvrable(current) and current not in jours_feries:
            compteur += 1
        current += timedelta(days=1)
    
    return compteur


def get_vacances_zone_b_data() -> Dict[int, List[Tuple[date, date, str]]]:
    """
    Retourne les données des vacances scolaires zone B.
    
    Format: {année: [(date_debut, date_fin, nom), ...]}
    
    Note: Pour l'instant, retourne un dictionnaire vide.
    Les données peuvent être chargées depuis un fichier JSON ou une API.

    Returns:
        Dict[int, List[Tuple[date, date, str]]]: Dictionnaire des vacances par année
    """
    # TODO: Charger depuis un fichier JSON ou une API
    # Pour l'instant, retourner un dictionnaire vide
    # Les données peuvent être ajoutées manuellement ou via une migration de données
    return {}


def get_vacances_zone_b(annee: int) -> List[Tuple[date, date, str]]:
    """
    Retourne les périodes de vacances scolaires zone B pour une année donnée.
    
    Utilise le cache pour éviter de recalculer les vacances à chaque appel.

    Args:
        annee: Année civile

    Returns:
        List[Tuple[date, date, str]]: Liste des périodes (date_debut, date_fin, nom)
    """
    cache_key = f'vacances_zone_b_{annee}'
    vacances = cache.get(cache_key)
    
    if vacances is None:
        vacances_data = get_vacances_zone_b_data()
        vacances = vacances_data.get(annee, [])
        # Mettre en cache pour 1 an
        cache.set(cache_key, vacances, CACHE_DURATION_ONE_YEAR)
    
    return vacances


def est_dans_periode_principale(d: date) -> bool:
    """
    Vérifie si une date est dans la période principale (1er mai - 31 octobre).

    Args:
        d: Date à vérifier

    Returns:
        bool: True si dans période principale, False sinon
    """
    mois = d.month
    jour = d.day
    
    # Période principale: 1er mai (5) au 31 octobre (10)
    if mois == 5 and jour >= 1:
        return True
    if 6 <= mois <= 9:  # Juin à septembre
        return True
    if mois == 10 and jour <= 31:
        return True
    
    return False


def est_hors_periode_principale(d: date) -> bool:
    """
    Vérifie si une date est hors période principale (1er novembre - 30 avril).

    Args:
        d: Date à vérifier

    Returns:
        bool: True si hors période principale, False sinon
    """
    return not est_dans_periode_principale(d)





