# Generated by Django 4.1.5 on 2023-02-08 07:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0007_homepage_climate_title_homepage_enable_climate'),
    ]

    operations = [
        migrations.AddField(
            model_name='homepage',
            name='enable_weather_forecasts',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AlterField(
            model_name='homepage',
            name='climate_title',
            field=models.CharField(blank=True, default='Explore Current Conditions', max_length=100, null=True, verbose_name='Climate Title'),
        ),
    ]
