from wagtail.permission_policies.collections import CollectionOwnershipPermissionPolicy

from integrations.webicons.models import WebIcon

permission_policy = CollectionOwnershipPermissionPolicy(
    WebIcon,
    auth_model=WebIcon,
    owner_field_name='uploaded_by_user'
)
