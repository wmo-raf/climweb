from django.db import migrations
import wagtail.blocks
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0052_alter_aisettings_id_alter_backupsettings_provider'),
    ]

    operations = [
        migrations.AlterField(
            model_name='navigationsettings',
            name='footer_menu',
            field=wagtail.fields.StreamField([('navigation_item', wagtail.blocks.StructBlock([('label', wagtail.blocks.CharBlock(label='Label')), ('page', wagtail.blocks.PageChooserBlock(label='Page', required=False)), ('external_url', wagtail.blocks.URLBlock(label='External URL', required=False)), ('open_in_new_tab', wagtail.blocks.BooleanBlock(default=True, label='Open in new tab', required=False)), ('include_subpages', wagtail.blocks.BooleanBlock(label='Include Subpages', required=False)), ('large_submenu', wagtail.blocks.BooleanBlock(label='Large Submenu Dropdown', required=False)), ('sub_items', wagtail.blocks.StreamBlock([('sub_item', wagtail.blocks.StructBlock([('label', wagtail.blocks.CharBlock(label='Label')), ('page', wagtail.blocks.PageChooserBlock(label='Page', required=False)), ('external_url', wagtail.blocks.URLBlock(label='External URL', required=False)), ('open_in_new_tab', wagtail.blocks.BooleanBlock(default=True, label='Open in new tab', required=False)), ('is_action', wagtail.blocks.BooleanBlock(label='Show as action button', required=False))]))], required=False))]))], blank=True, null=True, use_json_field=True),
        ),
        migrations.AlterField(
            model_name='navigationsettings',
            name='main_menu',
            field=wagtail.fields.StreamField([('navigation_item', wagtail.blocks.StructBlock([('label', wagtail.blocks.CharBlock(label='Label')), ('page', wagtail.blocks.PageChooserBlock(label='Page', required=False)), ('external_url', wagtail.blocks.URLBlock(label='External URL', required=False)), ('open_in_new_tab', wagtail.blocks.BooleanBlock(default=True, label='Open in new tab', required=False)), ('include_subpages', wagtail.blocks.BooleanBlock(label='Include Subpages', required=False)), ('large_submenu', wagtail.blocks.BooleanBlock(label='Large Submenu Dropdown', required=False)), ('sub_items', wagtail.blocks.StreamBlock([('sub_item', wagtail.blocks.StructBlock([('label', wagtail.blocks.CharBlock(label='Label')), ('page', wagtail.blocks.PageChooserBlock(label='Page', required=False)), ('external_url', wagtail.blocks.URLBlock(label='External URL', required=False)), ('open_in_new_tab', wagtail.blocks.BooleanBlock(default=True, label='Open in new tab', required=False)), ('is_action', wagtail.blocks.BooleanBlock(label='Show as action button', required=False))]))], required=False))]))], blank=True, null=True, use_json_field=True),
        ),
    ]
