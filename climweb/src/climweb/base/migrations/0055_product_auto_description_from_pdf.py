from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0054_alter_navigationsettings_footer_menu_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='auto_description_from_pdf',
            field=models.BooleanField(
                default=False,
                help_text=(
                    'When a PDF is ingested, take its opening paragraph and use it as '
                    'the product description. Headings, dates and letterheads are '
                    'skipped. Leave off if your PDFs are scans or maps, which hold no '
                    'readable text. Descriptions you write yourself are never '
                    'overwritten.'
                ),
                verbose_name='Use first paragraph of PDF as description',
            ),
        ),
    ]
