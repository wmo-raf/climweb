# Generated by Django 4.2.3 on 2024-03-27 11:29

import alertwise.capeditor.blocks
from django.db import migrations
import wagtail.blocks
import wagtail.fields


class Migration(migrations.Migration):
    dependencies = [
        ('home', '0017_homemapsettings'),
    ]
    
    operations = [
        migrations.AlterField(
            model_name='homemapsettings',
            name='zoom_locations',
            field=wagtail.fields.StreamField([('boundary_block', wagtail.blocks.StructBlock(
                [('areaDesc', wagtail.blocks.TextBlock(label='Area/Region Name')),
                 ('default', wagtail.blocks.BooleanBlock(label='Default', required=False)), ('admin_level',
                                                                                             wagtail.blocks.ChoiceBlock(
                                                                                                 choices=[
                                                                                                     (0, 'Level 0'),
                                                                                                     (1, 'Level 1'),
                                                                                                     (2, 'Level 2'),
                                                                                                     (3, 'Level 3')],
                                                                                                 label='Administrative Level')),
                 ('boundary',
                  alertwise.capeditor.blocks.BoundaryFieldBlock(help_text='Click to select boundary on the map',
                                                                label='Boundary'))], label='Admin Boundary')), (
                                                  'polygon_block', wagtail.blocks.StructBlock(
                                                      [('areaDesc', wagtail.blocks.TextBlock(label='Area/Region Name')),
                                                       (
                                                           'default',
                                                           wagtail.blocks.BooleanBlock(label='Default',
                                                                                       required=False)), (
                                                           'polygon', alertwise.capeditor.blocks.PolygonFieldBlock(
                                                               help_text='Draw custom area on the map',
                                                               label='Polygon'))],
                                                      label='Draw Polygon'))], blank=True, use_json_field=True),
        ),
    ]
