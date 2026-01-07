"""
Service de calcul pour l'application fractionnement.
"""
import logging
from decimal import Decimal
from datetime import date, timedelta
from typing import Optional
from django.contrib.auth import get_user_model

from ..models import CycleHebdomadaire, PeriodeConge, ParametresAnnee
from ..utils import (
    compter_jours_ouvres,
    compter_jours_ouvrables,
    est_dans_periode_principale,
    est_hors_periode_principale,
    est_jour_ouvre,
    est_jour_ouvrable,
    get_jours_feries,
)
from ..constants import (
    DUREE_LEGALE_ANNUELLE,
    SEMAINES_ANNUELLES,
    CONGES_ANNUELS_BASE,
)

logger = logging.getLogger(__name__)

User = get_user_model()


def calculer_rtt_annuels(heures_semaine: Decimal, quotite_travail: Decimal) -> int:
    """
    Calcule le nombre de RTT annuels selon le cycle hebdomadaire.

    Formule: (heures_semaine * 52 - 1607) / heures_semaine * quotite

    Args:
        heures_semaine: Nombre d'heures travaillées par semaine
        quotite_travail: Quotité de travail (0.5 à 1.0)

    Returns:
        int: Nombre de RTT annuels (arrondi)
    """
    from ..constants import HEURES_SEMAINE_MIN

    if heures_semaine <= HEURES_SEMAINE_MIN:
        # Pas de RTT pour 35h ou moins
        return 0

    # Calcul des heures supplémentaires par rapport à la durée légale
    heures_annuelles = heures_semaine * Decimal(SEMAINES_ANNUELLES)
    heures_supplementaires = heures_annuelles - Decimal(DUREE_LEGALE_ANNUELLE)

    if heures_supplementaires <= 0:
        return 0

    # Calcul du nombre de RTT (heures supplémentaires / heures par semaine)
    rtt_decimal = (heures_supplementaires / heures_semaine) * quotite_travail

    # Arrondir à l'entier le plus proche
    return int(round(rtt_decimal))


def calculer_conges_annuels(quotite_travail: Decimal, jours_ouvres_ou_ouvrables: str = 'ouvres') -> Decimal:
    """
    Calcule le nombre de congés annuels proratisés selon la quotité.

    Args:
        quotite_travail: Quotité de travail (0.5 à 1.0)
        jours_ouvres_ou_ouvrables: Type de jours ('ouvres' ou 'ouvrables')

    Returns:
        Decimal: Nombre de jours de congés annuels (proratisé)
    """
    conges_base = Decimal(CONGES_ANNUELS_BASE)
    conges_proratises = conges_base * quotite_travail

    # Arrondir à 2 décimales
    return conges_proratises.quantize(Decimal('0.01'))


def calculer_jours_fractionnement(jours_hors_periode: int) -> int:
    """
    Calcule le nombre de jours de fractionnement selon les règles spécifiées.

    Règles:
    - 5, 6 ou 7 jours hors période principale → 1 jour de fractionnement
    - 8 jours et plus → 2 jours de fractionnement
    - Moins de 5 jours → 0 jour

    Args:
        jours_hors_periode: Nombre de jours de CA pris hors période principale

    Returns:
        int: Nombre de jours de fractionnement (0, 1 ou 2)
    """
    if jours_hors_periode < 5:
        return 0
    elif 5 <= jours_hors_periode <= 7:
        return 1
    else:  # 8 jours et plus
        return 2


def compter_jours_periode(
    date_debut: date,
    date_fin: date,
    jours_ouvres_ou_ouvrables: str = 'ouvres',
    exclure_feries: bool = True,
    annee: Optional[int] = None,
    debut_type: str = 'matin',
    fin_type: str = 'apres_midi'
) -> Decimal:
    """
    Compte le nombre de jours (ouvrés ou ouvrables) dans une période, en gérant les demi-journées.

    Args:
        date_debut: Date de début
        date_fin: Date de fin (incluse)
        jours_ouvres_ou_ouvrables: Type de jours ('ouvres' ou 'ouvrables')
        exclure_feries: Si True, exclut les jours fériés
        annee: Année pour calculer les jours fériés (si None, utilise année de date_debut)
        debut_type: 'matin' ou 'apres_midi'
        fin_type: 'matin' ou 'apres_midi'

    Returns:
        Decimal: Nombre de jours comptés
    """
    if annee is None:
        annee = date_debut.year

    # Compter les jours pleins
    if jours_ouvres_ou_ouvrables == 'ouvrables':
        jours_pleins = compter_jours_ouvrables(date_debut, date_fin, exclure_feries, annee)
    else:
        jours_pleins = compter_jours_ouvres(date_debut, date_fin, exclure_feries, annee)

    total_jours = Decimal(jours_pleins)

    # Ajuster pour les demi-journées SEULEMENT si le jour concerné a été compté
    # (c'est-à-dire s'il n'est pas férié ou week-end)

    # Vérifier si le jour de début est compté
    debut_compte = False
    if jours_ouvres_ou_ouvrables == 'ouvrables':
        debut_compte = est_jour_ouvrable(date_debut)
    else:
        debut_compte = est_jour_ouvre(date_debut)

    if exclure_feries and debut_compte:
        jours_feries = get_jours_feries(annee)
        if date_debut in jours_feries:
            debut_compte = False

    # Si le jour de début est compté et commence l'après-midi, on enlève 0.5
    if debut_compte and debut_type == 'apres_midi':
        total_jours -= Decimal('0.5')

    # Vérifier si le jour de fin est compté
    fin_compte = False
    if jours_ouvres_ou_ouvrables == 'ouvrables':
        fin_compte = est_jour_ouvrable(date_fin)
    else:
        fin_compte = est_jour_ouvre(date_fin)

    if exclure_feries and fin_compte:
        jours_feries = get_jours_feries(annee)
        if date_fin in jours_feries:
            fin_compte = False

    # Si le jour de fin est compté et finit le matin, on enlève 0.5
    if fin_compte and fin_type == 'matin':
        total_jours -= Decimal('0.5')

    # Cas particulier : même jour, début après-midi et fin matin -> impossible logiquement
    # mais si début après-midi et fin après-midi le même jour -> 0.5 jour
    # La logique ci-dessus gère ça : 1 jour plein - 0.5 (début PM) = 0.5

    return max(Decimal('0.0'), total_jours)


def get_jours_hors_periode_principale(user: User, annee: int) -> int:
    """
    Calcule le nombre total de jours de congés annuels pris hors période principale.

    Args:
        user: Utilisateur concerné
        annee: Année civile

    Returns:
        int: Nombre de jours de CA pris hors période principale

    Raises:
        ValueError: Si l'année est invalide
    """
    from ..constants import ANNEE_MIN, ANNEE_MAX

    if not isinstance(annee, int) or annee < ANNEE_MIN or annee > ANNEE_MAX:
        raise ValueError(f"Année invalide: {annee} (doit être entre {ANNEE_MIN} et {ANNEE_MAX})")

    # Récupérer les paramètres de l'année pour savoir si on compte jours ouvrés ou ouvrables
    try:
        parametres = ParametresAnnee.objects.get(user=user, annee=annee)
        jours_type = parametres.jours_ouvres_ou_ouvrables
    except ParametresAnnee.DoesNotExist:
        # Par défaut, utiliser jours ouvrés
        jours_type = 'ouvres'

    # Récupérer toutes les périodes de congés annuels pour l'année
    try:
        periodes = PeriodeConge.objects.filter(
            user=user,
            annee_civile=annee,
            type_conge='annuel'
        ).select_related('user')
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des périodes pour {user.email}, année {annee}: {e}")
        return 0

    total_jours_hors_periode = Decimal('0.0')

    for periode in periodes:
        # Compter les jours de cette période qui sont hors période principale
        try:
            # Déterminer les sous-périodes hors période principale
            # Période principale : 1er mai - 31 octobre
            # Hors période principale : 1er novembre - 30 avril

            date_debut = periode.date_debut
            date_fin = periode.date_fin
            debut_type = periode.debut_type
            fin_type = periode.fin_type
            jours_hors = Decimal('0.0')

            # Cas 1 : Période entièrement hors période principale (novembre à avril)
            # Une période est entièrement hors période principale si :
            # - Elle commence en novembre ou décembre ET se termine en novembre ou décembre
            # - OU elle commence en janvier à avril ET se termine en janvier à avril
            # - OU elle chevauche l'année (début en nov/déc, fin en janv/avril)
            periode_entiere_hors = (
                (date_debut.month >= 11 and date_fin.month >= 11)  # Nov-déc
                or (date_debut.month <= 4 and date_fin.month <= 4)  # Janv-avril
                or (date_debut.month >= 11 and date_fin.month <= 4)  # Chevauche année
            ) and not (date_debut.month >= 5 and date_debut.month <= 10)

            if periode_entiere_hors:
                # Toute la période est hors période principale
                jours_hors = compter_jours_periode(
                    date_debut, date_fin, jours_type, exclure_feries=True, annee=annee,
                    debut_type=debut_type, fin_type=fin_type
                )
            # Cas 2 : Période entièrement dans période principale (mai à octobre)
            elif date_debut.month >= 5 and date_fin.month <= 10:
                # Aucun jour hors période principale
                jours_hors = Decimal('0.0')
            # Cas 3 : Période qui chevauche les deux périodes
            else:
                # Calculer les sous-périodes hors période principale
                # Sous-période 1 : début jusqu'au 30 avril (si applicable)
                if date_debut.month <= 4:
                    fin_avril = date(annee, 4, 30)
                    date_fin_sous_periode = min(date_fin, fin_avril)

                    # Si la sous-période s'arrête avant la fin réelle, la fin est forcément 'apres_midi' (journée complète)
                    # Sauf si c'est la fin réelle
                    fin_type_sous = 'apres_midi'
                    if date_fin_sous_periode == date_fin:
                        fin_type_sous = fin_type

                    jours_hors += compter_jours_periode(
                        date_debut, date_fin_sous_periode, jours_type, exclure_feries=True, annee=annee,
                        debut_type=debut_type, fin_type=fin_type_sous
                    )

                # Sous-période 2 : 1er novembre jusqu'à la fin (si applicable)
                if date_fin.month >= 11:
                    debut_novembre = date(annee, 11, 1)
                    date_debut_sous_periode = max(date_debut, debut_novembre)

                    # Si la sous-période commence après le début réel, le début est forcément 'matin' (journée complète)
                    # Sauf si c'est le début réel
                    debut_type_sous = 'matin'
                    if date_debut_sous_periode == date_debut:
                        debut_type_sous = debut_type

                    jours_hors += compter_jours_periode(
                        date_debut_sous_periode, date_fin, jours_type, exclure_feries=True, annee=annee,
                        debut_type=debut_type_sous, fin_type=fin_type
                    )

            total_jours_hors_periode += jours_hors
        except Exception as e:
            logger.warning(
                f"Erreur lors du calcul des jours pour la période {periode.id} "
                f"({periode.date_debut} - {periode.date_fin}): {e}"
            )
            # Continuer avec les autres périodes

    # Arrondir à l'entier inférieur pour le calcul du fractionnement (règle FPT ?)
    # Ou garder les décimales ? Le modèle CalculFractionnement attend un IntegerField pour jours_hors_periode
    # Mais la règle dit "3 à 5 jours", donc 2.5 jours ne compte pas comme 3.
    # On retourne un int (partie entière) ou on change la signature pour retourner Decimal ?
    # Pour l'instant on retourne int pour compatibilité, mais on devrait probablement changer CalculFractionnement aussi.
    # Pour respecter la signature actuelle (-> int), on retourne la partie entière.
    return int(total_jours_hors_periode)


def calculer_fractionnement_complet(user: User, annee: int) -> dict:
    """
    Calcule le fractionnement complet pour un utilisateur et une année.

    Args:
        user: Utilisateur concerné
        annee: Année civile

    Returns:
        dict: Dictionnaire avec les résultats du calcul

    Raises:
        ValueError: Si l'année est invalide
    """
    try:
        jours_hors_periode = get_jours_hors_periode_principale(user, annee)
        jours_fractionnement = calculer_jours_fractionnement(jours_hors_periode)

        return {
            'jours_hors_periode': jours_hors_periode,
            'jours_fractionnement': jours_fractionnement,
            'annee': annee,
        }
    except ValueError as e:
        logger.error(f"Erreur de validation lors du calcul du fractionnement pour {user.email}, année {annee}: {e}")
        raise
    except Exception as e:
        logger.error(
            f"Erreur inattendue lors du calcul du fractionnement pour {user.email}, année {annee}: {e}",
            exc_info=True
        )
        raise
