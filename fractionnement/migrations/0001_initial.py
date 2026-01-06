"""
Migration initiale pour l'application fractionnement.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CycleHebdomadaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annee', models.IntegerField(db_index=True, help_text='Année civile de référence', verbose_name='année')),
                ('heures_semaine', models.DecimalField(decimal_places=2, help_text="Nombre d'heures travaillées par semaine (ex: 35, 37, 38, 39)", max_digits=4, verbose_name='heures par semaine')),
                ('quotite_travail', models.DecimalField(decimal_places=2, default=Decimal('1.00'), help_text='Quotité de travail (0.5 pour mi-temps, 1.0 pour temps complet)', max_digits=3, verbose_name='quotité de travail')),
                ('jours_ouvres_ou_ouvrables', models.CharField(choices=[('ouvres', 'Jours ouvrés (lundi-vendredi)'), ('ouvrables', 'Jours ouvrables (lundi-samedi)')], default='ouvres', help_text='Type de jours utilisés pour le calcul', max_length=10, verbose_name='jours orvrés ou ouvrables')),
                ('rtt_annuels', models.IntegerField(default=0, help_text='Nombre de RTT calculés automatiquement', verbose_name='RTT annuels')),
                ('conges_annuels', models.DecimalField(decimal_places=2, default=Decimal('25.00'), help_text='Nombre de jours de congés annuels (proratisé selon quotité)', max_digits=5, verbose_name='congés annuels')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='date de modification')),
                ('user', models.ForeignKey(db_index=True, help_text='Agent concerné par ce cycle', on_delete=django.db.models.deletion.CASCADE, related_name='cycles_hebdomadaires', to=settings.AUTH_USER_MODEL, verbose_name='utilisateur')),
            ],
            options={
                'verbose_name': 'cycle hebdomadaire',
                'verbose_name_plural': 'cycles hebdomadaires',
                'ordering': ['-annee', 'user'],
            },
        ),
        migrations.CreateModel(
            name='ParametresAnnee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annee', models.IntegerField(db_index=True, help_text='Année civile', verbose_name='année')),
                ('jours_ouvres_ou_ouvrables', models.CharField(choices=[('ouvres', 'Jours ouvrés (lundi-vendredi)'), ('ouvrables', 'Jours ouvrables (lundi-samedi)')], default='ouvres', help_text="Type de jours utilisés pour les calculs de l'année", max_length=10, verbose_name='jours orvrés ou ouvrables')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='date de modification')),
                ('user', models.ForeignKey(db_index=True, help_text='Agent concerné', on_delete=django.db.models.deletion.CASCADE, related_name='parametres_annees', to=settings.AUTH_USER_MODEL, verbose_name='utilisateur')),
            ],
            options={
                'verbose_name': 'paramètres année',
                'verbose_name_plural': 'paramètres années',
                'ordering': ['-annee', 'user'],
            },
        ),
        migrations.CreateModel(
            name='PeriodeConge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_debut', models.DateField(db_index=True, help_text='Date de début de la période de congés', verbose_name='date de début')),
                ('date_fin', models.DateField(db_index=True, help_text='Date de fin de la période de congés', verbose_name='date de fin')),
                ('type_conge', models.CharField(choices=[('annuel', 'Congés annuels'), ('rtt', 'RTT'), ('asa', 'ASA (Autorisation Spéciale d\'Absence)'), ('maladie', 'Congé maladie'), ('autre', 'Autre')], db_index=True, default='annuel', help_text='Type de congé pris', max_length=20, verbose_name='type de congé')),
                ('annee_civile', models.IntegerField(db_index=True, help_text='Année civile de référence (calculée automatiquement)', verbose_name='année civile')),
                ('nb_jours', models.IntegerField(default=0, help_text='Nombre de jours calculés automatiquement', verbose_name='nombre de jours')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='date de modification')),
                ('user', models.ForeignKey(db_index=True, help_text='Agent concerné', on_delete=django.db.models.deletion.CASCADE, related_name='periodes_conges', to=settings.AUTH_USER_MODEL, verbose_name='utilisateur')),
            ],
            options={
                'verbose_name': 'période de congé',
                'verbose_name_plural': 'périodes de congés',
                'ordering': ['-date_debut', 'user'],
            },
        ),
        migrations.CreateModel(
            name='CalculFractionnement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annee', models.IntegerField(db_index=True, help_text='Année civile de référence', verbose_name='année')),
                ('jours_hors_periode', models.IntegerField(default=0, help_text='Nombre de jours de congés annuels pris hors période principale (1er nov - 30 avr)', verbose_name='jours hors période principale')),
                ('jours_fractionnement', models.IntegerField(default=0, help_text='Nombre de jours de fractionnement obtenus (0, 1 ou 2)', verbose_name='jours de fractionnement')),
                ('date_calcul', models.DateTimeField(auto_now_add=True, db_index=True, help_text='Date et heure du calcul', verbose_name='date de calcul')),
                ('user', models.ForeignKey(db_index=True, help_text='Agent concerné', on_delete=django.db.models.deletion.CASCADE, related_name='calculs_fractionnement', to=settings.AUTH_USER_MODEL, verbose_name='utilisateur')),
            ],
            options={
                'verbose_name': 'calcul de fractionnement',
                'verbose_name_plural': 'calculs de fractionnement',
                'ordering': ['-annee', 'user'],
            },
        ),
        migrations.AddIndex(
            model_name='periodeconge',
            index=models.Index(fields=['user', 'annee_civile'], name='fractionnem_periode_user_annee_idx'),
        ),
        migrations.AddIndex(
            model_name='periodeconge',
            index=models.Index(fields=['date_debut', 'date_fin'], name='fractionnem_periode_dates_idx'),
        ),
        migrations.AddIndex(
            model_name='periodeconge',
            index=models.Index(fields=['user', 'date_debut'], name='fractionnem_periode_user_date_idx'),
        ),
        migrations.AddIndex(
            model_name='cyclehebdomadaire',
            index=models.Index(fields=['user', 'annee'], name='fractionnem_cycle_user_annee_idx'),
        ),
        migrations.AddIndex(
            model_name='cyclehebdomadaire',
            index=models.Index(fields=['annee'], name='fractionnem_cycle_annee_idx'),
        ),
        migrations.AddIndex(
            model_name='parametresannee',
            index=models.Index(fields=['user', 'annee'], name='fractionnem_param_user_annee_idx'),
        ),
        migrations.AddIndex(
            model_name='calculfractionnement',
            index=models.Index(fields=['user', 'annee'], name='fractionnem_calc_user_annee_idx'),
        ),
        migrations.AddIndex(
            model_name='calculfractionnement',
            index=models.Index(fields=['annee'], name='fractionnem_calc_annee_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='parametresannee',
            unique_together={('user', 'annee')},
        ),
        migrations.AlterUniqueTogether(
            name='cyclehebdomadaire',
            unique_together={('user', 'annee')},
        ),
        migrations.AlterUniqueTogether(
            name='calculfractionnement',
            unique_together={('user', 'annee')},
        ),
    ]

