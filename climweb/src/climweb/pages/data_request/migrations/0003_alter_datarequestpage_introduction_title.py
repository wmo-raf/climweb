# Generated by Django 4.2.18 on 2025-01-29 08:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_request', '0002_alter_datarequestformfield_field_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datarequestpage',
            name='introduction_title',
            field=models.CharField(max_length=255, verbose_name='Introduction Title'),
        ),
    ]
