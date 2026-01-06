"""
Migration pour ajouter la relation ManyToMany secteurs au modèle User.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_user_email_verification_token_and_more'),
        ('secteurs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='secteurs',
            field=models.ManyToManyField(
                blank=True,
                help_text="Secteurs d'activité associés à cet utilisateur",
                related_name='utilisateurs',
                to='secteurs.secteur',
                verbose_name='secteurs'
            ),
        ),
    ]












