import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0001_initial"),
        ("base", "0047_merge_20260716_1407"),
    ]

    operations = [
        migrations.CreateModel(
            name="AISettings",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enabled", models.BooleanField(default=False, help_text="When enabled, AI writing tools appear in the rich text editor. You must select a provider and enter an API key below first.", verbose_name="Enable AI assistant")),
                ("provider", models.CharField(choices=[("openai", "OpenAI"), ("anthropic", "Anthropic (Claude)")], default="openai", help_text="The AI service to use. Choose the one you have an API key for.", max_length=20, verbose_name="Provider")),
                ("model_id", models.CharField(blank=True, help_text="Leave blank to use a sensible default for the selected provider (OpenAI: gpt-4o-mini, Claude: claude-3.5-haiku). Only set this if you want a specific model.", max_length=100, verbose_name="Model (optional)")),
                ("api_key", models.CharField(blank=True, max_length=512, verbose_name="API key")),
                ("site", models.OneToOneField(db_index=True, editable=False, on_delete=django.db.models.deletion.CASCADE, to="wagtailcore.site", unique=True)),
            ],
            options={
                "verbose_name": "AI Assistant",
            },
        ),
    ]
