# Generated by Django 4.2.18 on 2025-01-27 11:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0012_alter_servicepage_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='servicepage',
            name='introduction_button_text',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Introduction button text'),
        ),
    ]
