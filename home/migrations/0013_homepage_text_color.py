# Generated by Django 4.1.5 on 2023-02-08 08:01

from django.db import migrations
import wagtail_color_panel.fields


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0012_alter_homepage_hero_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='homepage',
            name='text_color',
            field=wagtail_color_panel.fields.ColorField(blank=True, max_length=7, null=True),
        ),
    ]
