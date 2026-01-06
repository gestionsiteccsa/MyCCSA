"""
Modèles de l'application events.
"""
from typing import List, Dict, Any
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from secteurs.models import Secteur

User = get_user_model()


class EventAddress(models.Model):
    """
    Modèle représentant l'adresse d'un événement.
    """
    rue = models.CharField(
        _('rue'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Numéro et nom de la rue')
    )
    ville = models.CharField(
        _('ville'),
        max_length=100,
        db_index=True,
        help_text=_('Ville où se déroule l\'événement')
    )
    code_postal = models.CharField(
        _('code postal'),
        max_length=20,
        blank=True,
        null=True,
        help_text=_('Code postal')
    )
    pays = models.CharField(
        _('pays'),
        max_length=100,
        blank=True,
        null=True,
        default='France',
        help_text=_('Pays')
    )
    complement = models.TextField(
        _('complément d\'adresse'),
        blank=True,
        null=True,
        help_text=_('Informations complémentaires (étage, bâtiment, etc.)')
    )

    class Meta:
        verbose_name = _('adresse d\'événement')
        verbose_name_plural = _('adresses d\'événements')

    def __str__(self) -> str:
        """
        Retourne la représentation string de l'adresse.

        Returns:
            str: Adresse formatée
        """
        parts = []
        if self.rue:
            parts.append(self.rue)
        if self.code_postal and self.ville:
            parts.append(f"{self.code_postal} {self.ville}")
        elif self.ville:
            parts.append(self.ville)
        if self.pays and self.pays != 'France':
            parts.append(self.pays)
        return ', '.join(parts) if parts else self.ville or ''


class Event(models.Model):
    """
    Modèle représentant un événement.
    """
    titre = models.CharField(
        _('titre'),
        max_length=200,
        db_index=True,
        help_text=_('Titre de l\'événement')
    )
    description = models.TextField(
        _('description'),
        blank=True,
        null=True,
        help_text=_('Description détaillée de l\'événement')
    )
    lieu = models.CharField(
        _('lieu'),
        max_length=200,
        blank=True,
        null=True,
        help_text=_('Nom du lieu (ex: Salle de réunion, Mairie, etc.)')
    )
    adresse = models.OneToOneField(
        EventAddress,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='event',
        verbose_name=_('adresse'),
        help_text=_('Adresse complète de l\'événement')
    )
    date_debut = models.DateTimeField(
        _('date de début'),
        db_index=True,
        help_text=_('Date et heure de début de l\'événement')
    )
    date_fin = models.DateTimeField(
        _('date de fin'),
        blank=True,
        null=True,
        db_index=True,
        help_text=_('Date et heure de fin de l\'événement (optionnel)')
    )
    secteurs = models.ManyToManyField(
        Secteur,
        related_name='evenements',
        blank=True,
        verbose_name=_('secteurs'),
        help_text=_('Secteurs associés à l\'événement')
    )
    couleur_calendrier = models.CharField(
        _('couleur calendrier'),
        max_length=7,
        blank=True,
        help_text=_('Couleur pour l\'affichage dans le calendrier (calculée automatiquement)')
    )
    createur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='evenements_crees',
        verbose_name=_('créateur'),
        db_index=True,
        help_text=_('Agent ayant créé l\'événement')
    )
    timezone = models.CharField(
        _('fuseau horaire'),
        max_length=50,
        default='Europe/Paris',
        help_text=_('Fuseau horaire de l\'événement')
    )
    date_publication_avant_le = models.DateField(
        _('date de publication avant le'),
        blank=True,
        null=True,
        help_text=_('Date avant laquelle l\'événement doit être publié sur les réseaux sociaux (information pour la communication)')
    )
    created_at = models.DateTimeField(
        _('date de création'),
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(
        _('date de modification'),
        auto_now=True
    )

    # Validation DGA/DGS
    STATUT_VALIDATION_CHOICES = [
        ('non_demande', _('Non demandé')),
        ('en_attente', _('En attente')),
        ('valide', _('Validé')),
        ('refuse', _('Refusé')),
    ]

    demande_validation_dga = models.BooleanField(
        _('demande validation DGA'),
        default=False,
        help_text=_('Demander une validation au DGA')
    )
    demande_validation_dgs = models.BooleanField(
        _('demande validation DGS'),
        default=False,
        help_text=_('Demander une validation au DGS')
    )
    statut_validation_dga = models.CharField(
        _('statut validation DGA'),
        max_length=20,
        choices=STATUT_VALIDATION_CHOICES,
        default='non_demande',
        db_index=True
    )
    statut_validation_dgs = models.CharField(
        _('statut validation DGS'),
        max_length=20,
        choices=STATUT_VALIDATION_CHOICES,
        default='non_demande',
        db_index=True
    )
    date_validation_dga = models.DateTimeField(
        _('date validation DGA'),
        null=True,
        blank=True
    )
    date_validation_dgs = models.DateTimeField(
        _('date validation DGS'),
        null=True,
        blank=True
    )
    validateur_dga = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validations_dga',
        verbose_name=_('validateur DGA')
    )
    validateur_dgs = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validations_dgs',
        verbose_name=_('validateur DGS')
    )
    commentaire_validation_dga = models.TextField(
        _('commentaire validation DGA'),
        blank=True,
        null=True
    )
    commentaire_validation_dgs = models.TextField(
        _('commentaire validation DGS'),
        blank=True,
        null=True
    )

    @property
    def statut_global_validation(self) -> str:
        """
        Retourne le statut global de validation.

        Returns:
            str: 'non_demande', 'en_attente', 'valide', ou 'refuse'
        """
        # Si aucune validation n'est demandée
        if not self.demande_validation_dga and not self.demande_validation_dgs:
            return 'non_demande'

        # Si une des validations est refusée
        if self.statut_validation_dga == 'refuse' or self.statut_validation_dgs == 'refuse':
            return 'refuse'

        # Si toutes les validations demandées sont validées
        dga_ok = not self.demande_validation_dga or self.statut_validation_dga == 'valide'
        dgs_ok = not self.demande_validation_dgs or self.statut_validation_dgs == 'valide'
        if dga_ok and dgs_ok:
            return 'valide'

        # Sinon, en attente
        return 'en_attente'

    @property
    def couleur_statut_validation(self) -> str:
        """
        Retourne la couleur CSS pour le statut de validation.

        Returns:
            str: Classe CSS de couleur de bordure
        """
        statut = self.statut_global_validation
        if statut == 'en_attente':
            return 'border-orange-400'
        elif statut == 'valide':
            return 'border-green-500'
        elif statut == 'refuse':
            return 'border-red-500'
        return 'border-gray-200'


    class Meta:
        verbose_name = _('événement')
        verbose_name_plural = _('événements')
        ordering = ['date_debut']
        indexes = [
            models.Index(fields=['date_debut']),
            models.Index(fields=['date_fin']),
            models.Index(fields=['createur']),
            models.Index(fields=['date_debut', 'date_fin']),
            # Index composites pour optimiser les requêtes fréquentes
            models.Index(fields=['statut_validation_dga', 'statut_validation_dgs']),
            models.Index(fields=['createur', 'date_debut']),
            models.Index(fields=['date_debut', 'statut_validation_dga']),
        ]

    def clean(self) -> None:
        """
        Valide les données de l'événement.

        Raises:
            ValidationError: Si les données sont invalides
            
        Example:
            >>> event = Event(titre='Test', date_debut=now, date_fin=now - timedelta(days=1))
            >>> event.clean()  # Raises ValidationError
        """
        super().clean()
        
        # Vérifier que date_fin >= date_debut si date_fin est renseignée
        if self.date_fin and self.date_debut and self.date_fin < self.date_debut:
            raise ValidationError({
                'date_fin': _('La date de fin doit être postérieure à la date de début.')
            })

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Sauvegarde l'événement et calcule la couleur du calendrier.
        
        Calcule automatiquement la couleur du calendrier en fonction des secteurs
        associés après la sauvegarde initiale.

        Args:
            *args: Arguments positionnels passés à Model.save()
            **kwargs: Arguments nommés passés à Model.save()
            
        Example:
            >>> event = Event.objects.create(titre='Test', date_debut=now, createur=user)
            >>> event.secteurs.add(secteur1)
            >>> event.save()  # Recalcule automatiquement la couleur
        """
        self.full_clean()  # Appeler la validation
        super().save(*args, **kwargs)
        
        # Calculer la couleur du calendrier basée sur les secteurs APRÈS la sauvegarde
        # (pour pouvoir accéder à la relation ManyToMany qui nécessite un id)
        self.couleur_calendrier = self._calculate_calendar_color()
        
        # Sauvegarder à nouveau pour enregistrer la couleur calculée
        if self.couleur_calendrier:
            super().save(update_fields=['couleur_calendrier'])

    def _calculate_calendar_color(self) -> str:
        """
        Calcule la couleur du calendrier en fonction des secteurs.
        
        Optimisé pour éviter les requêtes multiples : charge les secteurs une seule fois
        et travaille en mémoire.

        Returns:
            str: Code couleur hexadécimal
            
        Example:
            >>> event = Event.objects.create(...)
            >>> event.secteurs.add(secteur1, secteur2)
            >>> color = event._calculate_calendar_color()
            >>> assert color.startswith('#')
        """
        # Ne pas accéder à la relation ManyToMany si l'événement n'a pas encore de pk
        if not self.pk:
            # Couleur par défaut si l'événement n'est pas encore sauvegardé
            return '#808080'  # Gris
        
        # Charger les secteurs une seule fois et convertir en liste pour travailler en mémoire
        # Cela évite les requêtes multiples (exists(), count(), first())
        secteurs_list = list(self.secteurs.all())
        
        if not secteurs_list:
            # Couleur par défaut si aucun secteur
            return '#808080'  # Gris
        
        if len(secteurs_list) == 1:
            # Un seul secteur : utiliser sa couleur
            return secteurs_list[0].couleur
        
        # Plusieurs secteurs : calculer la couleur moyenne/mixte
        return self._mix_colors([s.couleur for s in secteurs_list])

    def _mix_colors(self, colors: List[str]) -> str:
        """
        Mélange plusieurs couleurs hexadécimales pour obtenir une couleur moyenne.
        
        Calcule la moyenne arithmétique des composantes RGB de chaque couleur.

        Args:
            colors: Liste de codes couleurs hex (ex: ['#FF0000', '#00FF00'])

        Returns:
            str: Code couleur hexadécimal mélangé
            
        Example:
            >>> event = Event()
            >>> mixed = event._mix_colors(['#FF0000', '#00FF00'])
            >>> assert mixed.startswith('#')
        """
        if not colors:
            return '#808080'
        
        # Convertir les couleurs hex en RGB
        rgb_values = []
        for color in colors:
            color = color.lstrip('#')
            if len(color) == 6:
                r = int(color[0:2], 16)
                g = int(color[2:4], 16)
                b = int(color[4:6], 16)
                rgb_values.append((r, g, b))
        
        if not rgb_values:
            return '#808080'
        
        # Calculer la moyenne de chaque composante RGB
        avg_r = sum(r for r, g, b in rgb_values) // len(rgb_values)
        avg_g = sum(g for r, g, b in rgb_values) // len(rgb_values)
        avg_b = sum(b for r, g, b in rgb_values) // len(rgb_values)
        
        # Convertir en hex
        return f"#{avg_r:02x}{avg_g:02x}{avg_b:02x}".upper()

    def __str__(self) -> str:
        """
        Retourne la représentation string de l'événement.

        Returns:
            str: Titre de l'événement
        """
        return self.titre


class EventFile(models.Model):
    """
    Modèle représentant un fichier attaché à un événement.
    """
    TYPE_FICHIER_CHOICES = [
        ('image', _('Image')),
        ('pdf', _('PDF')),
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='fichiers',
        verbose_name=_('événement'),
        db_index=True
    )
    fichier = models.FileField(
        _('fichier'),
        upload_to='events/files/%Y/%m/%d/',
        help_text=_('Fichier à joindre (image ou PDF, max 10 MB)')
    )
    type_fichier = models.CharField(
        _('type de fichier'),
        max_length=10,
        choices=TYPE_FICHIER_CHOICES,
        db_index=True,
        help_text=_('Type de fichier')
    )
    nom = models.CharField(
        _('nom'),
        max_length=255,
        help_text=_('Nom original du fichier')
    )
    taille = models.PositiveIntegerField(
        _('taille'),
        help_text=_('Taille du fichier en bytes')
    )
    uploaded_at = models.DateTimeField(
        _('date d\'upload'),
        auto_now_add=True,
        db_index=True
    )
    ordre = models.PositiveIntegerField(
        _('ordre'),
        default=0,
        db_index=True,
        help_text=_('Ordre d\'affichage du fichier')
    )

    class Meta:
        verbose_name = _('fichier d\'événement')
        verbose_name_plural = _('fichiers d\'événements')
        ordering = ['ordre', 'uploaded_at']
        indexes = [
            models.Index(fields=['event', 'ordre']),
            models.Index(fields=['type_fichier']),
        ]

    def __str__(self) -> str:
        """
        Retourne la représentation string du fichier.

        Returns:
            str: Nom du fichier
        """
        return self.nom
