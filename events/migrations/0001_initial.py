"""
Migration initiale pour l'application events.
"""
# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('secteurs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rue', models.CharField(blank=True, help_text='Numéro et nom de la rue', max_length=255, null=True, verbose_name='rue')),
                ('ville', models.CharField(db_index=True, help_text="Ville où se déroule l'événement", max_length=100, verbose_name='ville')),
                ('code_postal', models.CharField(blank=True, help_text='Code postal', max_length=20, null=True, verbose_name='code postal')),
                ('pays', models.CharField(blank=True, default='France', help_text='Pays', max_length=100, null=True, verbose_name='pays')),
                ('complement', models.TextField(blank=True, help_text='Informations complémentaires (étage, bâtiment, etc.)', null=True, verbose_name="complément d'adresse")),
            ],
            options={
                'verbose_name': "adresse d'événement",
                'verbose_name_plural': "adresses d'événements",
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titre', models.CharField(db_index=True, help_text="Titre de l'événement", max_length=200, verbose_name='titre')),
                ('description', models.TextField(blank=True, help_text="Description détaillée de l'événement", null=True, verbose_name='description')),
                ('lieu', models.CharField(blank=True, help_text='Nom du lieu (ex: Salle de réunion, Mairie, etc.)', max_length=200, null=True, verbose_name='lieu')),
                ('date_debut', models.DateTimeField(db_index=True, help_text='Date et heure de début de l\'événement', verbose_name='date de début')),
                ('date_fin', models.DateTimeField(blank=True, db_index=True, help_text='Date et heure de fin de l\'événement (optionnel)', null=True, verbose_name='date de fin')),
                ('couleur_calendrier', models.CharField(blank=True, help_text='Couleur pour l\'affichage dans le calendrier (calculée automatiquement)', max_length=7, verbose_name='couleur calendrier')),
                ('timezone', models.CharField(default='Europe/Paris', help_text='Fuseau horaire de l\'événement', max_length=50, verbose_name='fuseau horaire')),
                ('type_recurrence', models.CharField(choices=[('none', 'Aucune récurrence (jour unique)'), ('daily', 'Quotidien'), ('weekly', 'Hebdomadaire'), ('monthly', 'Mensuel'), ('yearly', 'Annuel'), ('custom', 'Personnalisé (jours spécifiques)')], db_index=True, default='none', help_text='Type de récurrence de l\'événement', max_length=20, verbose_name='type de récurrence')),
                ('jours_recurrence', models.JSONField(blank=True, help_text='Jours de la semaine pour la récurrence personnalisée (ex: [1, 3, 5] pour lun, mer, ven)', null=True, verbose_name='jours de récurrence')),
                ('date_fin_recurrence', models.DateField(blank=True, help_text='Date à laquelle la récurrence s\'arrête', null=True, verbose_name='date de fin de récurrence')),
                ('occurrences', models.PositiveIntegerField(blank=True, help_text='Nombre d\'occurrences (optionnel, alternative à date_fin_recurrence)', null=True, verbose_name='nombre d\'occurrences')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='date de modification')),
                ('adresse', models.OneToOneField(blank=True, help_text='Adresse complète de l\'événement', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='event', to='events.eventaddress', verbose_name='adresse')),
                ('createur', models.ForeignKey(db_index=True, help_text='Agent ayant créé l\'événement', on_delete=django.db.models.deletion.CASCADE, related_name='evenements_crees', to=settings.AUTH_USER_MODEL, verbose_name='créateur')),
            ],
            options={
                'verbose_name': 'événement',
                'verbose_name_plural': 'événements',
                'ordering': ['date_debut'],
            },
        ),
        migrations.CreateModel(
            name='EventFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fichier', models.FileField(help_text='Fichier à joindre (image ou PDF, max 10 MB)', upload_to='events/files/%Y/%m/%d/', verbose_name='fichier')),
                ('type_fichier', models.CharField(choices=[('image', 'Image'), ('pdf', 'PDF')], db_index=True, help_text='Type de fichier', max_length=10, verbose_name='type de fichier')),
                ('nom', models.CharField(help_text='Nom original du fichier', max_length=255, verbose_name='nom')),
                ('taille', models.PositiveIntegerField(help_text='Taille du fichier en bytes', verbose_name='taille')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='date d\'upload')),
                ('ordre', models.PositiveIntegerField(db_index=True, default=0, help_text='Ordre d\'affichage du fichier', verbose_name='ordre')),
                ('event', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='fichiers', to='events.event', verbose_name='événement')),
            ],
            options={
                'verbose_name': 'fichier d\'événement',
                'verbose_name_plural': 'fichiers d\'événements',
                'ordering': ['ordre', 'uploaded_at'],
            },
        ),
        migrations.AddField(
            model_name='event',
            name='secteurs',
            field=models.ManyToManyField(blank=True, help_text='Secteurs associés à l\'événement', related_name='evenements', to='secteurs.secteur', verbose_name='secteurs'),
        ),
        migrations.AddIndex(
            model_name='eventfile',
            index=models.Index(fields=['event', 'ordre'], name='events_even_event_id_ordre_idx'),
        ),
        migrations.AddIndex(
            model_name='eventfile',
            index=models.Index(fields=['type_fichier'], name='events_even_type_fi_idx'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['date_debut'], name='events_even_date_de_idx'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['date_fin'], name='events_even_date_fi_idx'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['createur'], name='events_even_createu_idx'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['type_recurrence'], name='events_even_type_re_idx'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['date_debut', 'date_fin'], name='events_even_date_de_date_fi_idx'),
        ),
    ]













