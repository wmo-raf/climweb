# Generated by Django 4.2.18 on 2025-02-04 09:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0003_remove_newstype_is_alert_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='newspage',
            name='feature_img_src',
        ),
    ]
