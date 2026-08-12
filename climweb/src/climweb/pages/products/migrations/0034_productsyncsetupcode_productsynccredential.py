import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('base', '0054_alter_navigationsettings_footer_menu_and_more'),
        ('products', '0033_add_gif_product_block'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductSyncCredential',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(help_text='Hostname reported by the server that set this up.', max_length=255, verbose_name='Server')),
                ('token_hash', models.CharField(db_index=True, max_length=64, unique=True)),
                ('token_prefix', models.CharField(help_text='First characters of the token, to tell credentials apart.', max_length=12, verbose_name='Token')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('last_used_at', models.DateTimeField(blank=True, null=True, verbose_name='Last Used')),
                ('last_used_ip', models.GenericIPAddressField(blank=True, null=True, verbose_name='Last Used From')),
                ('upload_count', models.PositiveIntegerField(default=0, verbose_name='Files Received')),
                ('revoked_at', models.DateTimeField(blank=True, null=True, verbose_name='Revoked At')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sync_credentials', to='base.product', verbose_name='Product')),
            ],
            options={
                'verbose_name': 'Product Sync Credential',
                'verbose_name_plural': 'Product Sync Credentials',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProductSyncSetupCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, unique=True, verbose_name='Setup Code')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('expires_at', models.DateTimeField(verbose_name='Expires At')),
                ('used_at', models.DateTimeField(blank=True, null=True, verbose_name='Used At')),
                ('used_by_host', models.CharField(blank=True, max_length=255, verbose_name='Used By Host')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sync_setup_codes', to='base.product', verbose_name='Product')),
            ],
            options={
                'verbose_name': 'Product Sync Setup Code',
                'verbose_name_plural': 'Product Sync Setup Codes',
                'ordering': ['-created_at'],
            },
        ),
    ]
