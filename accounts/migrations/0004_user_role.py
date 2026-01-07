"""
Migration pour ajouter la relation ForeignKey role au modèle User.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_user_secteurs'),
        ('role', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.ForeignKey(
                blank=True,
                help_text="Rôle hiérarchique de l'utilisateur",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='utilisateurs',
                to='role.role',
                verbose_name='rôle'
            ),
        ),
    ]










