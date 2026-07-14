# Generated manually to match climweb.pages.shortlinks.models.ShortLink.source

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shortlinks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='shortlink',
            name='source',
            field=models.CharField(
                choices=[('admin', 'Created in admin'), ('public', 'Submitted via public form')],
                default='admin',
                editable=False,
                help_text='Whether this link was created by a logged-in editor or submitted anonymously via the '
                          'public form.',
                max_length=10,
                verbose_name='Source',
            ),
        ),
    ]
