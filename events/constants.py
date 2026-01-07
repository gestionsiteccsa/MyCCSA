"""
Constantes de l'application events.
"""
# Taille maximale des fichiers : 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB en bytes

# Types de fichiers acceptés
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
ALLOWED_PDF_TYPES = ['application/pdf']
ALLOWED_FILE_TYPES = ALLOWED_IMAGE_TYPES + ALLOWED_PDF_TYPES

# Maximum de fichiers par événement
MAX_FILES_PER_EVENT = 5

# Taille maximale des images pour compression (1920x1080)
MAX_IMAGE_WIDTH = 1920
MAX_IMAGE_HEIGHT = 1080

# Qualité de compression JPEG par défaut
DEFAULT_JPEG_QUALITY = 85

# Limite d'événements dans la timeline
TIMELINE_EVENTS_LIMIT = 200

# Durée du cache pour les vues (en secondes)
CACHE_DURATION_CALENDAR = 60 * 5  # 5 minutes

# Rate limiting pour les uploads
RATE_LIMIT_UPLOADS_PER_MINUTE = 10  # Maximum 10 uploads par minute par utilisateur

# Timezones autorisés pour les événements
ALLOWED_TIMEZONES = [
    'Europe/Paris',
    'UTC',
    'America/New_York',
    'America/Los_Angeles',
    'Asia/Tokyo',
]

# Durée du cache pour les statistiques (en secondes)
CACHE_DURATION_STATS = 60 * 10  # 10 minutes
