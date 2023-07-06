# Generated by Django 4.1.9 on 2023-07-06 13:36

from django.db import migrations
import wagtail.blocks
import wagtail.contrib.table_block.blocks
import wagtail.fields
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('flex_page', '0007_alter_flexpage_content'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flexpage',
            name='content',
            field=wagtail.fields.StreamField([('title_text', wagtail.blocks.StructBlock([('title', wagtail.blocks.CharBlock(help_text='Section title', max_length=100, verbose_name='Section Title')), ('text', wagtail.blocks.RichTextBlock(features=['bold', 'ul', 'ol', 'link', 'superscript', 'subscript'], help_text='Section description', verbose_name='Section Text'))])), ('title_text_image', wagtail.blocks.StructBlock([('title', wagtail.blocks.CharBlock(help_text='Section title', max_length=100, verbose_name='Section Title')), ('text', wagtail.blocks.RichTextBlock(features=['bold', 'ul', 'ol', 'link', 'superscript', 'subscript'], help_text='Section description', verbose_name='Section Text')), ('image', wagtail.images.blocks.ImageChooserBlock(required=False))])), ('accordion', wagtail.blocks.StructBlock([('title', wagtail.blocks.CharBlock(required=True)), ('collapsibles', wagtail.blocks.StreamBlock([('collapsibles', wagtail.blocks.StructBlock([('heading', wagtail.blocks.CharBlock()), ('description', wagtail.blocks.RichTextBlock(features=['bold', 'ul', 'ol', 'link', 'superscript', 'subscript'])), ('image', wagtail.images.blocks.ImageChooserBlock(required=False))]))]))])), ('table', wagtail.blocks.StructBlock([('title', wagtail.blocks.CharBlock(required=True)), ('table', wagtail.contrib.table_block.blocks.TableBlock())]))], blank=True, null=True, use_json_field=True),
        ),
    ]
