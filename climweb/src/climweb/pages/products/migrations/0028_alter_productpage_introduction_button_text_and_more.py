# Generated by Django 4.2.18 on 2025-03-20 12:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0027_productpage_menu_order_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productpage',
            name='introduction_button_text',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Introduction button text'),
        ),
        migrations.AlterField(
            model_name='subnationalproductpage',
            name='introduction_button_text',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Introduction button text'),
        ),
    ]
