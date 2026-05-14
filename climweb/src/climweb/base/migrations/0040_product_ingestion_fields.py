from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0039_alter_theme_border_radius'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='variable_name',
            field=models.SlugField(
                blank=True,
                help_text="Folder name for this product, e.g. 'daily_forecast'. "
                          "Used as the top-level folder in the watch root path.",
                verbose_name='Variable Name',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='temporal_resolution',
            field=models.CharField(
                blank=True,
                choices=[
                    ('yearly', 'Yearly'),
                    ('monthly', 'Monthly'),
                    ('weekly', 'Weekly'),
                    ('daily', 'Daily'),
                    ('hourly', 'Hourly'),
                    ('dekadal', 'Dekadal'),
                    ('pentadal', 'Pentadal'),
                ],
                max_length=20,
                verbose_name='Temporal Resolution',
                help_text='Determines the default filename date convention for product item types.',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='watch_root',
            field=models.CharField(
                blank=True,
                max_length=500,
                verbose_name='Watch Root Path',
                help_text='Absolute filesystem path that contains the {variable_name} folder. '
                          'Full scan path: {watch_root}/{variable_name}/{format}/{name_convention}.{format}',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='ingestion_enabled',
            field=models.BooleanField(
                default=False,
                verbose_name='Enable Auto-Ingestion',
                help_text='When enabled, the system will periodically scan the watch root for new files.',
            ),
        ),
        migrations.AddField(
            model_name='productcategory',
            name='category_format',
            field=models.CharField(
                blank=True,
                max_length=20,
                verbose_name='File Format',
                help_text="The file format/extension for this category, e.g. 'png', 'pdf', 'jpg'. "
                          "This also determines the subfolder name: {variable_name}/{format}/",
            ),
        ),
        migrations.AddField(
            model_name='productitemtype',
            name='file_name_convention',
            field=models.CharField(
                blank=True,
                max_length=500,
                verbose_name='Filename Convention',
                help_text=(
                    'Filename pattern used to match and parse product files (without extension). '
                    'Use {yyyy} for year, {mm} for month, {dd} for day, {hh} for hour. '
                    'Auto-populated from the product temporal resolution. '
                    "You may add a prefix or suffix, e.g. 'temp_{yyyy}_{mm}_{dd}_00_00_00'."
                ),
            ),
        ),
    ]
