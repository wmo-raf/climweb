# Generated by Django 4.2.3 on 2023-08-30 09:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0020_alter_productitemtype_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productcategory',
            name='icon',
            field=models.CharField(default='folder-inverse', max_length=100, verbose_name='Icon'),
        ),
    ]
