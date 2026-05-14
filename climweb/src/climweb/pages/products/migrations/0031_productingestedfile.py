from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0040_product_ingestion_fields'),
        ('products', '0030_subnationalproductslandingpage'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductIngestedFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_path', models.CharField(max_length=1000, verbose_name='File Path')),
                ('file_mtime', models.FloatField(verbose_name='File Modification Time')),
                ('ingested_at', models.DateTimeField(auto_now_add=True, verbose_name='Ingested At')),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ingested_files',
                    to='base.product',
                    verbose_name='Product',
                )),
                ('product_item_page', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='ingested_files',
                    to='products.productitempage',
                    verbose_name='Product Item Page',
                )),
            ],
            options={
                'verbose_name': 'Product Ingested File',
                'verbose_name_plural': 'Product Ingested Files',
            },
        ),
        migrations.AlterUniqueTogether(
            name='productingestedfile',
            unique_together={('product', 'file_path')},
        ),
    ]
