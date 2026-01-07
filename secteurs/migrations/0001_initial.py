"""
Migration initiale pour l'application secteurs.
"""
# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Secteur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(db_index=True, help_text="Nom du secteur d'activité", max_length=200, unique=True, verbose_name='nom')),
                ('couleur', models.CharField(help_text='Code couleur hexadécimal (ex: #1f4d9b)', max_length=7, verbose_name='couleur')),
                ('ordre', models.PositiveIntegerField(db_index=True, default=0, help_text="Ordre d'affichage du secteur", verbose_name='ordre')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='date de modification')),
            ],
            options={
                'verbose_name': 'secteur',
                'verbose_name_plural': 'secteurs',
                'ordering': ['ordre', 'nom'],
            },
        ),
        migrations.AddIndex(
            model_name='secteur',
            index=models.Index(fields=['nom'], name='secteurs_se_nom_idx'),
        ),
        migrations.AddIndex(
            model_name='secteur',
            index=models.Index(fields=['ordre'], name='secteurs_se_ordre_idx'),
        ),
        migrations.AddIndex(
            model_name='secteur',
            index=models.Index(fields=['-created_at'], name='secteurs_se_created_idx'),
        ),
    ]













