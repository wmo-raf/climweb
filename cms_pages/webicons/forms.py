from django.forms import ModelForm
from wagtail.admin.forms.collections import BaseCollectionMemberForm, collection_member_permission_formset_factory
from cms_pages.webicons.fields import SVGField
from cms_pages.webicons.models import WebIcon
from .permissions import permission_policy as icons_permission_policy


class WebIconForm(BaseCollectionMemberForm, ModelForm):
    permission_policy = icons_permission_policy
    file = SVGField()

    class Meta:
        model = WebIcon
        fields = "__all__"


GroupIconPermissionFormSet = collection_member_permission_formset_factory(
    WebIcon,
    [
        ('add_webicon', ("Add"), ("Add/edit icons you own")),
        ('change_webicon', ("Edit"), ("Edit any icon")),
    ],
    'webicons/permissions/includes/icon_permissions_formset.html'
)
