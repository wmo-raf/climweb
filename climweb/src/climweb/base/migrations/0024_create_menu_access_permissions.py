from django.db import migrations

permissions = [
    ('can_view_geomanager_menu', 'Can view Geomanager menu'),
    ('can_view_survey_menu', 'Can View Survey menu'),
    ('can_view_alerts_menu', 'Can view CAP Alerts Menu'),
    ('can_view_forecast_menu', 'Can view Forecast Menu')
]


def create_menu_access_permissions(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")
    Permission = apps.get_model("auth.Permission")
    Group = apps.get_model("auth.Group")

    # Add a content type to hang the 'can access Wagtail admin' permission off
    perm_content_type, created = ContentType.objects.get_or_create(
        app_label="base", model="menupermission"
    )

    # Create permissions
    for permission in permissions:
        admin_permission, created = Permission.objects.get_or_create(
            content_type=perm_content_type,
            codename=permission[0],
            name=permission[1],
        )

        # Assign it to Editors and Moderators groups
        for group in Group.objects.filter(name__in=["Editors", "Moderators"]):
            group.permissions.add(admin_permission)


def remove_menu_access_permissions(apps, schema_editor):
    """Reverse the above additions of permissions."""
    ContentType = apps.get_model("contenttypes.ContentType")
    Permission = apps.get_model("auth.Permission")
    perm_content_type = ContentType.objects.get(
        app_label="base",
        model="menupermission",
    )

    for permission in permissions:
        # This cascades to Group
        Permission.objects.filter(
            content_type=perm_content_type,
            codename=permission[0],
        ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('base', '0023_menupermission'),
        # We cannot apply and unapply this migration unless GroupCollectionPermission
        # is created. #2529
        ("wagtailcore", "0026_group_collection_permission"),
    ]

    operations = [
        migrations.RunPython(
            create_menu_access_permissions, remove_menu_access_permissions
        ),
    ]
