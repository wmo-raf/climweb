# Generated by Django 4.2.18 on 2025-03-20 12:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenders', '0002_tenderspage_introduction_button_link_external'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tenderspage',
            name='introduction_button_text',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Introduction button text'),
        ),
    ]
