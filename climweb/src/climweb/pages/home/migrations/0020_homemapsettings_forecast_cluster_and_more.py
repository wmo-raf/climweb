# Generated by Django 4.2.7 on 2024-11-13 09:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0019_homepage_pre_title_alter_homepage_hero_subtitle_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='homemapsettings',
            name='forecast_cluster',
            field=models.BooleanField(default=False, verbose_name='Cluster Location Forecast Points'),
        ),
        migrations.AddField(
            model_name='homemapsettings',
            name='forecast_cluster_min_points',
            field=models.PositiveIntegerField(blank=True, default=2, help_text='Minimum number of points necessary to form a cluster if clustering is enabled', null=True, verbose_name='Cluster Minimum number of Points'),
        ),
        migrations.AddField(
            model_name='homemapsettings',
            name='forecast_cluster_radius',
            field=models.PositiveIntegerField(blank=True, default=50, help_text='Radius of each cluster if clustering is enabled', null=True, verbose_name='Cluster Radius'),
        ),
    ]
