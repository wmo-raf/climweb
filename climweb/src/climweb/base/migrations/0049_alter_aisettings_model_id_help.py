from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("base", "0048_aisettings"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aisettings",
            name="model_id",
            field=models.CharField(
                blank=True,
                help_text=(
                    "Leave blank to use a sensible default for the selected provider "
                    "(OpenAI: gpt-4o-mini, Claude: claude-haiku-4.5). Only set this if "
                    "you want a specific model. Provider model names change over time; if "
                    "you get a 'model not found' error, enter a current one here."
                ),
                max_length=100,
                verbose_name="Model (optional)",
            ),
        ),
    ]
