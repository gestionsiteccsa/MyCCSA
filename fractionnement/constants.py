"""
Constantes pour l'application fractionnement.
"""
from decimal import Decimal

# Limites d'années
ANNEE_MIN = 2020
ANNEE_MAX = 2100

# Limites d'heures par semaine
HEURES_SEMAINE_MIN = Decimal('35')
HEURES_SEMAINE_MAX = Decimal('39')

# Limites de quotité de travail
QUOTITE_TRAVAIL_MIN = Decimal('0.5')
QUOTITE_TRAVAIL_MAX = Decimal('1.0')

# Durée légale annuelle en heures
DUREE_LEGALE_ANNUELLE = 1607

# Nombre de semaines dans une année
SEMAINES_ANNUELLES = 52

# Congés annuels de base (jours) - Decimal pour compatibilité avec les modèles
CONGES_ANNUELS_BASE = Decimal('25.00')

# Pagination
PAGINATION_PAR_PAGE = 25

# Durée du cache en secondes (1 an)
CACHE_DURATION_ONE_YEAR = 31536000

