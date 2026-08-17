# Generated manually to match climweb.pages.shortlinks.models.ShortLink

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ShortLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_code', models.CharField(blank=True, help_text='Leave blank to auto-generate. Only letters, numbers, - and _ are allowed. This is the part that appears after /s/ in the short link.', max_length=15, unique=True, verbose_name='Short code')),
                ('target_url', models.URLField(help_text='The full URL this short link should redirect visitors to.', max_length=2000, verbose_name='Target URL')),
                ('label', models.CharField(blank=True, help_text='Optional note to help editors remember what this link is for.', max_length=255, verbose_name='Label')),
                ('is_active', models.BooleanField(default=True, help_text='Untick to disable this short link without deleting it.', verbose_name='Active')),
                ('click_count', models.PositiveIntegerField(default=0, editable=False, verbose_name='Click count')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('created_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Created by')),
            ],
            options={
                'verbose_name': 'Short Link',
                'verbose_name_plural': 'Short Links',
                'ordering': ['-created_at'],
            },
        ),
    ]
