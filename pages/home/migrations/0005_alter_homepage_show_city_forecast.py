# Generated by Django 4.2.2 on 2023-08-09 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0004_remove_homepage_enable_mapviewer_cta_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homepage',
            name='show_city_forecast',
            field=models.BooleanField(default=True, verbose_name='Show city forecast section'),
        ),
    ]
