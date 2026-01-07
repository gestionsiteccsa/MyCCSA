"""
Migration initiale pour l'application role.
"""
# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(db_index=True, help_text='Nom du rôle hiérarchique', max_length=200, unique=True, verbose_name='nom')),
                ('niveau', models.PositiveIntegerField(db_index=True, help_text='Niveau hiérarchique (0 = agents, 1 = coordo, 2 = directeur, etc.)', unique=True, verbose_name='niveau')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='date de modification')),
            ],
            options={
                'verbose_name': 'rôle',
                'verbose_name_plural': 'rôles',
                'ordering': ['niveau', 'nom'],
            },
        ),
        migrations.AddIndex(
            model_name='role',
            index=models.Index(fields=['nom'], name='role_role_nom_idx'),
        ),
        migrations.AddIndex(
            model_name='role',
            index=models.Index(fields=['niveau'], name='role_role_niveau_idx'),
        ),
        migrations.AddIndex(
            model_name='role',
            index=models.Index(fields=['-created_at'], name='role_role_created_idx'),
        ),
    ]











