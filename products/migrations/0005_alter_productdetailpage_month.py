# Generated by Django 4.1.7 on 2023-03-01 00:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_productspage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productdetailpage',
            name='month',
            field=models.IntegerField(choices=[(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')], default=3),
        ),
    ]
