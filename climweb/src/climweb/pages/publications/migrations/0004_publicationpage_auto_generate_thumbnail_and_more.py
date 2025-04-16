# Generated by Django 4.2.18 on 2025-04-16 07:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0027_image_description'),
        ('publications', '0003_alter_publicationsindexpage_earliest_publication_year'),
    ]

    operations = [
        migrations.AddField(
            model_name='publicationpage',
            name='auto_generate_thumbnail',
            field=models.BooleanField(default=True, help_text='If the document is a PDF, an image of the first page will be auto-generated.', verbose_name='Auto-generate thumbnail'),
        ),
        migrations.AlterField(
            model_name='publicationpage',
            name='thumbnail',
            field=models.ForeignKey(blank=True, help_text='This can be a screenshot of the front page of the publication. If left empty and the uploaded document is a PDF, an image of the first page will be auto-generated.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.image', verbose_name='Publication image'),
        ),
    ]
