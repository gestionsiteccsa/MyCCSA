"""
Migration pour créer les rôles initiaux.
"""
from django.db import migrations


def populate_initial_roles(apps, schema_editor):
    """
    Crée les 5 rôles initiaux avec leurs niveaux.

    Args:
        apps: Registry des applications
        schema_editor: Éditeur de schéma
    """
    Role = apps.get_model('role', 'Role')

    roles_data = [
        {'nom': 'Agents', 'niveau': 0},
        {'nom': 'Coordo', 'niveau': 1},
        {'nom': 'Directeur', 'niveau': 2},
        {'nom': 'DGA DGS', 'niveau': 3},
        {'nom': 'Élu', 'niveau': 4},
    ]

    for role_data in roles_data:
        # Vérifier si le rôle existe déjà
        if not Role.objects.filter(nom=role_data['nom']).exists():
            Role.objects.create(**role_data)


def reverse_populate_initial_roles(apps, schema_editor):
    """
    Supprime les rôles initiaux (fonction inverse).

    Args:
        apps: Registry des applications
        schema_editor: Éditeur de schéma
    """
    Role = apps.get_model('role', 'Role')

    noms_roles = [
        'Agents',
        'Coordo',
        'Directeur',
        'DGA DGS',
        'Élu',
    ]

    Role.objects.filter(nom__in=noms_roles).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('role', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            populate_initial_roles,
            reverse_populate_initial_roles
        ),
    ]











