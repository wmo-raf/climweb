# Generated by Django 4.1.7 on 2023-03-27 17:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_remove_importantpages_all_images_of_change_page_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='importantpages',
            name='all_forecasts_page',
        ),
    ]
