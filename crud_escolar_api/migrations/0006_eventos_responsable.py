# Generated by Django 4.2 on 2025-05-16 02:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crud_escolar_api', '0005_eventos'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventos',
            name='responsable',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
