# Generated by Django 4.1.7 on 2023-03-31 08:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0001_initial'),
        ('home', '0021_homepage_enable_media'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homepage',
            name='youtube_playlist',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='videos.youtubeplaylist'),
        ),
    ]
