# Generated by Django 4.1.5 on 2023-02-08 07:57

from django.db import migrations
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0010_homepage_hero_banner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homepage',
            name='hero_title',
            field=wagtail.fields.RichTextField(default='National Meteorological & Hydrological Services', max_length=100, null=True, verbose_name='Title'),
        ),
    ]
