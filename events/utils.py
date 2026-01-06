"""
Utilitaires pour l'application events.
"""
import logging
import os
from io import BytesIO
from typing import Optional, List
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from django.utils.text import slugify
import sys
from django.core.cache import cache
from .constants import (
    MAX_IMAGE_WIDTH,
    MAX_IMAGE_HEIGHT,
    DEFAULT_JPEG_QUALITY,
    CACHE_DURATION_CALENDAR,
)

logger = logging.getLogger(__name__)


def compress_and_optimize_image(
    image_file,
    quality: int = DEFAULT_JPEG_QUALITY
) -> Optional[InMemoryUploadedFile]:
    """
    Compresse et optimise une image pour réduire sa taille.
    
    Cette fonction :
    - Convertit les images en RGB (nécessaire pour JPEG)
    - Redimensionne les images trop grandes (max MAX_IMAGE_WIDTH x MAX_IMAGE_HEIGHT)
    - Compresse avec la qualité JPEG spécifiée
    - Optimise le fichier pour réduire la taille
    
    Args:
        image_file: Fichier image à compresser (peut être PNG, JPEG, GIF, WebP)
        quality: Qualité de compression JPEG (1-100, défaut: DEFAULT_JPEG_QUALITY)
                 Plus la qualité est élevée, plus le fichier est volumineux
    
    Returns:
        Optional[InMemoryUploadedFile]: Fichier compressé en mémoire ou None en cas d'erreur
        
    Example:
        >>> from django.core.files.uploadedfile import SimpleUploadedFile
        >>> image = SimpleUploadedFile("test.png", image_data, content_type="image/png")
        >>> compressed = compress_and_optimize_image(image, quality=80)
        >>> if compressed:
        >>>     print(f"Taille originale: {image.size}, Taille compressée: {compressed.size}")
        
    Note:
        Les images avec transparence (RGBA) sont converties en RGB avec un fond blanc.
        Les images trop grandes sont redimensionnées proportionnellement.
    """
    try:
        # Ouvrir l'image
        img = Image.open(image_file)
        
        # Convertir en RGB si nécessaire (pour JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Créer un fond blanc pour les images avec transparence
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensionner si l'image est trop grande
        max_size = (MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT)
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Sauvegarder dans un buffer mémoire
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        # Créer un nouveau fichier en mémoire
        compressed_file = InMemoryUploadedFile(
            output,
            'ImageField',
            image_file.name,
            'image/jpeg',
            sys.getsizeof(output),
            None
        )
        
        return compressed_file
    except Exception as e:
        logger.error(f"Erreur lors de la compression de l'image: {e}")
        return None


def process_event_images(event, images: List, existing_images_count: int = 0) -> int:
    """
    Traite et sauvegarde les images d'un événement.
    
    Cette fonction factorise le code dupliqué entre event_create_view et event_update_view.
    Elle gère :
    - La compression des images
    - La génération de noms de fichiers uniques (basés sur le slug de l'événement)
    - La numérotation séquentielle des images
    - La sauvegarde dans des transactions atomiques
    
    Args:
        event: Instance de l'événement (doit avoir un pk)
        images: Liste des fichiers image à traiter (peut être vide)
        existing_images_count: Nombre d'images existantes (pour la numérotation continue)
    
    Returns:
        int: Nombre d'images effectivement sauvegardées (peut être < len(images) en cas d'erreur)
        
    Example:
        >>> event = Event.objects.get(pk=1)
        >>> images = [image1, image2, image3]
        >>> existing_count = event.fichiers.filter(type_fichier='image').count()
        >>> saved = process_event_images(event, images, existing_count)
        >>> print(f"{saved} images sauvegardées sur {len(images)}")
        
    Note:
        Chaque image est traitée dans sa propre transaction pour éviter les verrouillages
        SQLite lors de la compression de fichiers volumineux.
        Les erreurs lors de la sauvegarde d'une image n'interrompent pas le traitement des autres.
    """
    from django.db import transaction
    from django.utils.text import slugify
    from .models import EventFile
    import os
    
    if not images:
        return 0
    
    # Générer le slug à partir du titre de l'événement
    event_slug = slugify(event.titre)
    
    saved_count = 0
    
    # Traiter chaque image dans sa propre transaction courte
    for index, image_file in enumerate(images):
        # Vérifier que c'est bien une image
        if image_file.content_type in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
            # Compresser l'image EN DEHORS de la transaction
            # (cette opération peut prendre du temps pour les gros fichiers)
            compressed_file = compress_and_optimize_image(image_file)
            if compressed_file:
                image_file = compressed_file
            
            # Générer le nouveau nom de fichier avec slug et numéro
            file_extension = os.path.splitext(image_file.name)[1] or '.jpg'
            image_number = existing_images_count + index + 1
            new_filename = f"{event_slug}-{image_number:02d}{file_extension}"
            
            # Renommer le fichier
            image_file.name = new_filename
            
            # Sauvegarder l'image dans une transaction courte
            try:
                with transaction.atomic():
                    # Recharger l'événement pour éviter les problèmes de cache
                    event.refresh_from_db()
                    
                    # Créer l'instance EventFile
                    event_file = EventFile(
                        event=event,
                        fichier=image_file,
                        type_fichier='image',
                        nom=new_filename,
                        taille=image_file.size,
                        ordre=existing_images_count + index
                    )
                    event_file.save()
                    saved_count += 1
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde de l'image {new_filename}: {e}")
                # Continuer avec les autres images
    
    return saved_count


def get_secteurs_for_display():
    """
    Récupère les secteurs pour l'affichage dans les formulaires.
    
    Utilise le cache pour éviter les requêtes répétées.
    
    Returns:
        list: Liste des secteurs ordonnés par ordre et nom
        
    Example:
        >>> secteurs = get_secteurs_for_display()
        >>> for secteur in secteurs:
        >>>     print(secteur.nom)
    """
    from secteurs.models import Secteur
    
    cache_key = 'secteurs_display'
    secteurs = cache.get(cache_key)
    
    if secteurs is None:
        secteurs = list(
            Secteur.objects.only('id', 'nom', 'couleur', 'ordre')
            .order_by('ordre', 'nom')
        )
        # Mettre en cache pour 5 minutes (même durée que le cache du calendrier)
        cache.set(cache_key, secteurs, CACHE_DURATION_CALENDAR)
    
    return secteurs
