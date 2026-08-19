# Updates the source field's choices/help_text after removing the public form.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shortlinks', '0002_shortlink_source'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shortlink',
            name='source',
            field=models.CharField(
                choices=[('admin', 'Created in admin'), ('public', 'Created by a site visitor')],
                default='admin',
                editable=False,
                help_text='Whether this link was created by a logged-in editor or by a visitor using the share '
                          'button.',
                max_length=10,
                verbose_name='Source',
            ),
        ),
    ]
