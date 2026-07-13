import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0089_log_entry_data_json_null_to_object'),
        ('tenders', '0003_alter_tenderspage_introduction_button_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenderdetailpage',
            name='apply_button_text',
            field=models.CharField(blank=True, default='Apply Now', max_length=50, null=True,
                                   verbose_name='Apply button text'),
        ),
        migrations.AddField(
            model_name='tenderdetailpage',
            name='application_page',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name='+', to='wagtailcore.page', verbose_name='Application Page'),
        ),
        migrations.AddField(
            model_name='tenderdetailpage',
            name='external_application_url',
            field=models.URLField(blank=True, max_length=500, null=True,
                                  verbose_name='External Application Link'),
        ),
    ]
