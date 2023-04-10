# Generated by Django 4.1.7 on 2023-04-10 12:25

from django.db import migrations
import wagtail_color_panel.fields


class Migration(migrations.Migration):

    dependencies = [
        ('site_settings', '0008_alter_theme_border_radius_alter_theme_box_shadow'),
    ]

    operations = [
        migrations.AddField(
            model_name='theme',
            name='primary_hover_color',
            field=wagtail_color_panel.fields.ColorField(blank=True, default='#67a9ce', help_text='Primary Hover color (use color picker)', max_length=7, null=True),
        ),
    ]
