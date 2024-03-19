# Generated by Django 4.2.3 on 2024-03-19 11:20

from django.db import migrations
import wagtail.blocks
import wagtail.contrib.table_block.blocks
import wagtail.documents.blocks
import wagtail.fields
import wagtail.images.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0021_alter_productitempage_products'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productitempage',
            name='products',
            field=wagtail.fields.StreamField([('image_product', wagtail.blocks.StructBlock([('product_type', wagtail.blocks.CharBlock(label='Product Type', required=True)), ('date', wagtail.blocks.DateBlock(help_text='The date when this product becomes effective', label='Effective from', required=True)), ('valid_until', wagtail.blocks.DateBlock(help_text='The last day this product remains effective. Leave blank if not applicable', label='Effective until', required=False)), ('image', wagtail.images.blocks.ImageChooserBlock(label='Image', required=True)), ('description', wagtail.blocks.RichTextBlock(label='Summary of the map/image information', required=False))], label='Map/Image Product')), ('document_product', wagtail.blocks.StructBlock([('product_type', wagtail.blocks.CharBlock(label='Product Type', required=True)), ('thumbnail', wagtail.images.blocks.ImageChooserBlock(help_text='For example a screen grab of the cover page', label='Thumbnail of the document', required=False)), ('date', wagtail.blocks.DateBlock(help_text='The date when this product becomes effective', label='Effective from', required=True)), ('valid_until', wagtail.blocks.DateBlock(help_text='The last day this product remains effective. Leave blank if not applicable', label='Effective until', required=False)), ('document', wagtail.documents.blocks.DocumentChooserBlock(label='Document', required=True)), ('description', wagtail.blocks.RichTextBlock(label='Summary of the document information', required=False))], label='Document/Bulletin Product')), ('content_block', wagtail.blocks.StructBlock([('product_type', wagtail.blocks.CharBlock(label='Product Type', required=True)), ('date', wagtail.blocks.DateBlock(help_text='The date when this product becomes effective', label='Effective from', required=True)), ('valid_until', wagtail.blocks.DateBlock(help_text='The last day this product remains effective. Leave blank if not applicable', label='Effective until', required=False)), ('content', wagtail.blocks.StreamBlock([('table', wagtail.contrib.table_block.blocks.TableBlock(label='Table')), ('text', wagtail.blocks.RichTextBlock(label='Text'))], label='Content'))], label='Text/Tabular Product'))], use_json_field=True),
        ),
    ]
