# Generated by Django 4.1.7 on 2023-03-31 07:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0006_eventpage_feature_img_src'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eventpage',
            name='feature_img_src',
        ),
    ]
