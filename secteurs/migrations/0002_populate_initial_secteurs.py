"""
Migration pour créer les secteurs initiaux.
"""
from django.db import migrations


def populate_initial_secteurs(apps, schema_editor):
    """
    Crée les 11 secteurs initiaux avec leurs couleurs.

    Args:
        apps: Registry des applications
        schema_editor: Éditeur de schéma
    """
    Secteur = apps.get_model('secteurs', 'Secteur')

    secteurs_data = [
        {'nom': 'SANTÉ', 'couleur': '#b4c7e7', 'ordre': 1},
        {'nom': 'RURALITÉ', 'couleur': '#005b24', 'ordre': 2},
        {'nom': 'CONVENTION TERRITORIALE GLOBALE', 'couleur': '#7030a0', 'ordre': 3},
        {'nom': 'DÉVELOPPEMENT ÉCONOMIQUE', 'couleur': '#1f4d9b', 'ordre': 4},
        {'nom': 'SERVICES TECHNIQUES & ENVIRONNEMENT', 'couleur': '#a9d18e', 'ordre': 5},
        {'nom': 'RÉSEAU MÉDI@\'PASS', 'couleur': '#bfe1dd', 'ordre': 6},
        {'nom': 'POLITIQUE DU LOGEMENT ET DU CADRE DE VIE', 'couleur': '#ffc000', 'ordre': 7},
        {'nom': 'SERVICES SUPPORTS (RH/FINANCES...)', 'couleur': '#ff6699', 'ordre': 8},
        {'nom': 'MOBILITÉ', 'couleur': '#ff0000', 'ordre': 9},
        {'nom': 'PROMOTION DU TOURISME ET DU TERRITOIRE', 'couleur': '#92d050', 'ordre': 10},
        {'nom': 'PARTENARIATS', 'couleur': '#e74f12', 'ordre': 11},
    ]

    for secteur_data in secteurs_data:
        # Vérifier si le secteur existe déjà
        if not Secteur.objects.filter(nom=secteur_data['nom']).exists():
            Secteur.objects.create(**secteur_data)


def reverse_populate_initial_secteurs(apps, schema_editor):
    """
    Supprime les secteurs initiaux (fonction inverse).

    Args:
        apps: Registry des applications
        schema_editor: Éditeur de schéma
    """
    Secteur = apps.get_model('secteurs', 'Secteur')

    noms_secteurs = [
        'SANTÉ',
        'RURALITÉ',
        'CONVENTION TERRITORIALE GLOBALE',
        'DÉVELOPPEMENT ÉCONOMIQUE',
        'SERVICES TECHNIQUES & ENVIRONNEMENT',
        'RÉSEAU MÉDI@\'PASS',
        'POLITIQUE DU LOGEMENT ET DU CADRE DE VIE',
        'SERVICES SUPPORTS (RH/FINANCES...)',
        'MOBILITÉ',
        'PROMOTION DU TOURISME ET DU TERRITOIRE',
        'PARTENARIATS',
    ]

    Secteur.objects.filter(nom__in=noms_secteurs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('secteurs', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            populate_initial_secteurs,
            reverse_populate_initial_secteurs
        ),
    ]












