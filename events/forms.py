"""
Formulaires de l'application events.
"""
import os
from typing import Any, Dict, Optional
from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models import Event, EventFile, EventAddress
from .utils import compress_and_optimize_image
from .constants import (
    MAX_FILE_SIZE,
    ALLOWED_IMAGE_TYPES,
    ALLOWED_PDF_TYPES,
    ALLOWED_FILE_TYPES,
    MAX_FILES_PER_EVENT,
    ALLOWED_TIMEZONES,
)
from secteurs.models import Secteur

User = get_user_model()


class EventAddressForm(forms.ModelForm):
    """
    Formulaire pour l'adresse d'un événement.
    """
    class Meta:
        model = EventAddress
        fields = ['rue', 'ville', 'code_postal', 'pays', 'complement']
        widgets = {
            'rue': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'placeholder': _('Numéro et nom de la rue')
            }),
            'ville': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'placeholder': _('Ville')
            }),
            'code_postal': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'placeholder': _('Code postal')
            }),
            'pays': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'placeholder': _('Pays')
            }),
            'complement': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'rows': 3,
                'placeholder': _('Informations complémentaires (étage, bâtiment, etc.)')
            }),
        }

    def clean_ville(self) -> str:
        """
        Valide que la ville est renseignée.

        Returns:
            str: Ville nettoyée

        Raises:
            ValidationError: Si la ville est vide

        Example:
            >>> form = EventAddressForm({'ville': '  Paris  '})
            >>> form.is_valid()
            >>> assert form.cleaned_data['ville'] == 'Paris'
        """
        ville = self.cleaned_data.get('ville')
        if not ville or not ville.strip():
            raise ValidationError(_('La ville est obligatoire.'))
        return ville.strip()


class EventFileForm(forms.ModelForm):
    """
    Formulaire pour un fichier d'événement.
    """
    class Meta:
        model = EventFile
        fields = ['fichier', 'ordre']
        widgets = {
            'fichier': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'accept': 'image/*,.pdf'
            }),
            'ordre': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'min': 0
            }),
        }

    def clean_fichier(self) -> Optional[UploadedFile]:
        """
        Valide le fichier uploadé.

        Vérifie la taille et le type MIME du fichier.

        Returns:
            UploadedFile: Fichier validé ou None si aucun fichier

        Raises:
            ValidationError: Si le fichier est invalide (taille ou type)

        Example:
            >>> form = EventFileForm({'fichier': large_file})
            >>> form.is_valid()  # Raises ValidationError si fichier trop gros
        """
        fichier = self.cleaned_data.get('fichier')
        if not fichier:
            return fichier

        # Vérifier la taille
        if fichier.size > MAX_FILE_SIZE:
            raise ValidationError(
                _('Le fichier est trop volumineux. Taille maximale : %(size)s MB') % {
                    'size': MAX_FILE_SIZE // (1024 * 1024)
                }
            )

        # Vérifier le type MIME déclaré
        content_type = fichier.content_type
        if content_type not in ALLOWED_FILE_TYPES:
            raise ValidationError(
                _('Type de fichier non autorisé. Types acceptés : images (JPEG, PNG, GIF, WebP) et PDF.')
            )

        # Validation stricte : Vérifier le type réel du fichier (pas seulement le content_type)
        # pour éviter les attaques par falsification du type MIME
        try:
            # Sauvegarder la position du fichier
            fichier.seek(0)

            if content_type in ALLOWED_IMAGE_TYPES:
                # Pour les images, utiliser Pillow pour vérifier le type réel
                from PIL import Image
                try:
                    img = Image.open(fichier)
                    # Vérifier que l'image peut être ouverte et que le format est valide
                    img.verify()
                    # Réinitialiser le pointeur après vérification
                    fichier.seek(0)
                except Exception:
                    raise ValidationError(
                        _('Le fichier image est corrompu ou n\'est pas une image valide.')
                    )
            elif content_type == 'application/pdf':
                # Pour les PDF, vérifier les premiers bytes (magic number)
                fichier.seek(0)
                header = fichier.read(4)
                fichier.seek(0)
                # Les PDF commencent par %PDF
                if not header.startswith(b'%PDF'):
                    raise ValidationError(
                        _('Le fichier n\'est pas un PDF valide.')
                    )
        except ValidationError:
            # Re-raise les ValidationError
            raise
        except Exception as e:
            # Pour les autres erreurs, logger et lever une ValidationError générique
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Erreur lors de la validation du fichier: {e}")
            raise ValidationError(
                _('Impossible de valider le type du fichier. Veuillez réessayer.')
            )

        return fichier

    def save(self, commit: bool = True) -> EventFile:
        """
        Sauvegarde le fichier avec les métadonnées.

        Compresse automatiquement les images avant sauvegarde.

        Args:
            commit: Si True, sauvegarde en base de données

        Returns:
            EventFile: Instance du fichier sauvegardé

        Example:
            >>> form = EventFileForm({'fichier': image_file})
            >>> if form.is_valid():
            >>>     event_file = form.save()
        """
        instance = super().save(commit=False)

        if instance.fichier:
            # Déterminer le type de fichier
            content_type = instance.fichier.content_type
            if content_type in ALLOWED_IMAGE_TYPES:
                instance.type_fichier = 'image'

                # Compresser l'image si c'est une image
                compressed_file = compress_and_optimize_image(instance.fichier)
                if compressed_file:
                    # Remplacer le fichier original par le fichier compressé
                    instance.fichier = compressed_file
                    # Mettre à jour la taille
                    instance.taille = compressed_file.size
                else:
                    # Si la compression a échoué, utiliser l'original
                    instance.taille = instance.fichier.size

            elif content_type in ALLOWED_PDF_TYPES:
                instance.type_fichier = 'pdf'
                instance.taille = instance.fichier.size

            # Stocker le nom original
            instance.nom = instance.fichier.name

        if commit:
            instance.save()

        return instance


class EventForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier un événement.
    """
    # Champs pour l'adresse (inline)
    adresse_rue = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
            'placeholder': _('Numéro et nom de la rue')
        })
    )
    adresse_ville = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
            'placeholder': _('Ville')
        })
    )
    adresse_code_postal = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
            'placeholder': _('Code postal')
        })
    )
    adresse_pays = forms.CharField(
        required=False,
        initial='France',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
            'placeholder': _('Pays')
        })
    )
    adresse_complement = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
            'rows': 3,
            'placeholder': _('Informations complémentaires')
        })
    )

    # Champ pour la date de publication
    date_publication_avant_le = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
            'type': 'date'
        })
    )
    date_publication_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-custom-blue border-gray-300 rounded focus:ring-custom-blue'
        })
    )

    # Champs pour la demande de validation DGA/DGS
    demande_validation_dga = forms.BooleanField(
        required=False,
        label=_('Demander validation DGA'),
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-orange-500 border-gray-300 rounded focus:ring-orange-500'
        })
    )
    demande_validation_dgs = forms.BooleanField(
        required=False,
        label=_('Demander validation DGS'),
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-orange-500 border-gray-300 rounded focus:ring-orange-500'
        })
    )

    class Meta:
        model = Event
        fields = [
            'titre', 'description', 'lieu', 'date_debut', 'date_fin',
            'secteurs', 'timezone', 'demande_validation_dga', 'demande_validation_dgs'
        ]
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'placeholder': _('Titre de l\'événement')
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'rows': 5,
                'placeholder': _('Description de l\'événement')
            }),
            'lieu': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'placeholder': _('Nom du lieu')
            }),
            'date_debut': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'type': 'datetime-local'
            }),
            'date_fin': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent',
                'type': 'datetime-local'
            }),
            'secteurs': forms.CheckboxSelectMultiple(attrs={
                'class': 'space-y-2'
            }),
            'timezone': forms.Select(
                choices=[
                    ('Europe/Paris', 'Europe/Paris (UTC+1)'),
                    ('UTC', 'UTC'),
                    ('America/New_York', 'America/New_York (UTC-5)'),
                    ('America/Los_Angeles', 'America/Los_Angeles (UTC-8)'),
                    ('Asia/Tokyo', 'Asia/Tokyo (UTC+9)'),
                ],
                attrs={
                    'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-custom-blue focus:border-transparent'
                }
            ),
        }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialise le formulaire.

        Configure les querysets et pré-remplit les champs si l'événement existe.

        Args:
            *args: Arguments positionnels
            **kwargs: Arguments nommés (peut contenir 'instance' pour modification)
        """
        super().__init__(*args, **kwargs)

        # Configurer le queryset des secteurs
        self.fields['secteurs'].queryset = Secteur.objects.all().order_by('ordre', 'nom')
        self.fields['secteurs'].required = False

        # Rendre timezone non obligatoire (valeur par défaut sera ajoutée dans la vue)
        self.fields['timezone'].required = False

        # Pré-remplir les champs d'adresse si l'événement existe
        if self.instance and self.instance.pk and self.instance.adresse:
            adresse = self.instance.adresse
            self.fields['adresse_rue'].initial = adresse.rue
            self.fields['adresse_ville'].initial = adresse.ville
            self.fields['adresse_code_postal'].initial = adresse.code_postal
            self.fields['adresse_pays'].initial = adresse.pays
            self.fields['adresse_complement'].initial = adresse.complement

        # Pré-remplir la date de publication si l'événement existe
        if self.instance and self.instance.pk and self.instance.date_publication_avant_le:
            self.fields['date_publication_avant_le'].initial = self.instance.date_publication_avant_le
            self.fields['date_publication_active'].initial = True

    def clean_date_fin(self) -> Optional[Any]:
        """
        Valide que date_fin >= date_debut.

        Returns:
            Optional[datetime]: Date de fin validée ou None

        Raises:
            ValidationError: Si date_fin < date_debut

        Example:
            >>> form = EventForm({'date_debut': '2024-01-02T10:00', 'date_fin': '2024-01-01T10:00'})
            >>> form.is_valid()  # False, ValidationError
        """
        date_debut = self.cleaned_data.get('date_debut')
        date_fin = self.cleaned_data.get('date_fin')

        if date_fin and date_debut and date_fin < date_debut:
            raise ValidationError(
                _('La date de fin doit être postérieure à la date de début.')
            )

        return date_fin

    def clean_date_publication_avant_le(self) -> Optional[Any]:
        """
        Valide la date de publication.

        Retourne None si la case n'est pas cochée ou si aucune date n'est fournie.

        Returns:
            Optional[date]: Date de publication validée ou None
        """
        date_publication_active = self.cleaned_data.get('date_publication_active', False)
        date_publication = self.cleaned_data.get('date_publication_avant_le')

        # Si la case est cochée mais pas de date, retourner None
        if date_publication_active and not date_publication:
            return None

        # Si la case n'est pas cochée, retourner None
        if not date_publication_active:
            return None

        return date_publication

    def clean_timezone(self) -> str:
        """
        Valide que le timezone est dans la liste autorisée.

        Returns:
            str: Timezone validé

        Raises:
            ValidationError: Si le timezone n'est pas autorisé

        Example:
            >>> form = EventForm({'timezone': 'Invalid/Timezone'})
            >>> form.is_valid()  # False, ValidationError
        """
        timezone = self.cleaned_data.get('timezone')
        if timezone and timezone not in ALLOWED_TIMEZONES:
            raise ValidationError(
                _('Timezone non autorisé. Veuillez choisir parmi les options disponibles.')
            )
        return timezone or 'Europe/Paris'

    def save(self, commit: bool = True) -> Event:
        """
        Sauvegarde l'événement et son adresse.

        Crée ou met à jour l'adresse associée si une ville est renseignée.
        Gère également les demandes de validation DGA/DGS.

        Args:
            commit: Si True, sauvegarde en base de données

        Returns:
            Event: Instance de l'événement sauvegardé

        Example:
            >>> form = EventForm({'titre': 'Test', 'date_debut': '2024-01-01T10:00'})
            >>> if form.is_valid():
            >>>     event = form.save(commit=False)
            >>>     event.createur = user
            >>>     event.save()
        """
        instance = super().save(commit=False)

        # Gérer l'adresse
        adresse_rue = self.cleaned_data.get('adresse_rue', '').strip()
        adresse_ville = self.cleaned_data.get('adresse_ville', '').strip()
        adresse_code_postal = self.cleaned_data.get('adresse_code_postal', '').strip()
        adresse_pays = self.cleaned_data.get('adresse_pays', '').strip() or 'France'
        adresse_complement = self.cleaned_data.get('adresse_complement', '').strip()

        # Créer ou mettre à jour l'adresse si la ville est renseignée
        if adresse_ville:
            if instance.adresse:
                adresse = instance.adresse
            else:
                adresse = EventAddress()

            adresse.rue = adresse_rue or None
            adresse.ville = adresse_ville
            adresse.code_postal = adresse_code_postal or None
            adresse.pays = adresse_pays or 'France'
            adresse.complement = adresse_complement or None
            adresse.save()
            instance.adresse = adresse
        elif instance.adresse:
            # Supprimer l'adresse si la ville n'est plus renseignée
            instance.adresse.delete()
            instance.adresse = None

        # Gérer la date de publication
        date_publication_active = self.cleaned_data.get('date_publication_active', False)
        if date_publication_active:
            instance.date_publication_avant_le = self.cleaned_data.get('date_publication_avant_le')
        else:
            instance.date_publication_avant_le = None

        # Gérer les demandes de validation DGA/DGS
        demande_dga = self.cleaned_data.get('demande_validation_dga', False)
        demande_dgs = self.cleaned_data.get('demande_validation_dgs', False)

        # Si une nouvelle demande de validation est faite, initialiser le statut à 'en_attente'
        # Pour une création (instance.pk is None) ou si la demande change
        if demande_dga:
            if instance.pk is None or not instance.demande_validation_dga:
                instance.statut_validation_dga = 'en_attente'
        else:
            instance.statut_validation_dga = 'non_demande'

        if demande_dgs:
            if instance.pk is None or not instance.demande_validation_dgs:
                instance.statut_validation_dgs = 'en_attente'
        else:
            instance.statut_validation_dgs = 'non_demande'

        instance.demande_validation_dga = demande_dga
        instance.demande_validation_dgs = demande_dgs

        if commit:
            instance.save()
            # Sauvegarder les secteurs (ManyToMany)
            self.save_m2m()

        return instance
