from capeditor.models import CapSetting
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.actions.copy_page import CopyPageAction
from wagtail.admin import messages
from wagtail.admin.forms.pages import CopyForm
from wagtail.admin.menu import MenuItem, Menu
from wagtail.models import Page
from wagtail_modeladmin.menus import GroupMenuItem
from wagtail_modeladmin.options import (
    ModelAdmin,
    modeladmin_register,
    ModelAdminGroup
)

from .models import CapAlertPage, CAPGeomanagerSettings
from .utils import create_cap_geomanager_dataset


class CAPAdmin(ModelAdmin):
    model = CapAlertPage
    menu_label = _('Alerts')
    menu_icon = 'list-ul'
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False


class CAPMenuGroupAdminMenuItem(GroupMenuItem):
    def is_shown(self, request):
        return request.user.has_perm("base.can_view_alerts_menu")


class CAPMenuGroup(ModelAdminGroup):
    menu_label = _('CAP Alerts')
    menu_icon = 'warning'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    items = (CAPAdmin,)

    def get_menu_item(self, order=None):
        if self.modeladmin_instances:
            submenu = Menu(items=self.get_submenu_items())
            return CAPMenuGroupAdminMenuItem(self, self.get_menu_order(), submenu)

    def get_submenu_items(self):
        menu_items = []
        item_order = 1

        for modeladmin in self.modeladmin_instances:
            menu_items.append(modeladmin.get_menu_item(order=item_order))
            item_order += 1

        try:

            # add settings menu
            settings_url = reverse(
                "wagtailsettings:edit",
                args=[CapSetting._meta.app_label, CapSetting._meta.model_name, ],
            )
            gm_settings_menu = MenuItem(label=_("CAP Base Settings"), url=settings_url, icon_name="cog")
            menu_items.append(gm_settings_menu)

            # add geomanager settings menu
            settings_url = reverse("wagtailsettings:edit",
                                   args=[CAPGeomanagerSettings._meta.app_label,
                                         CAPGeomanagerSettings._meta.model_name, ], )

            cap_geomanager_settings_menu = MenuItem(label=_("CAP Mapviewer Settings"), url=settings_url,
                                                    icon_name="cog")

            menu_items.append(cap_geomanager_settings_menu)

        except Exception:
            pass

        return menu_items


modeladmin_register(CAPMenuGroup)


@hooks.register('construct_settings_menu')
def hide_settings_menu_item(request, menu_items):
    hidden_settings = ["cap-settings", "cap-geomanager-settings"]
    menu_items[:] = [item for item in menu_items if item.name not in hidden_settings]


@hooks.register('register_geomanager_datasets')
def add_geomanager_datasets(request):
    datasets = []
    cap_geomanager_settings = CAPGeomanagerSettings.for_request(request)
    if cap_geomanager_settings.show_on_mapviewer and cap_geomanager_settings.geomanager_subcategory:

        # check if we have any live alerts
        has_live_alerts = CapAlertPage.objects.live().filter(status="Actual").exists()

        # create dataset
        dataset = create_cap_geomanager_dataset(cap_geomanager_settings, has_live_alerts, request)

        # add dataset to list
        if dataset:
            datasets.append(dataset)

    return datasets


@hooks.register("before_copy_page")
def copy_cap_alert_page(request, page):
    if page.specific.__class__.__name__ == "CapAlertPage":
        # Parent page defaults to parent of source page
        parent_page = page.get_parent()

        # Check if the user has permission to publish subpages on the parent
        can_publish = parent_page.permissions_for_user(request.user).can_publish_subpage()

        # Create the form
        form = CopyForm(
            request.POST or None, user=request.user, page=page, can_publish=can_publish
        )

        # Remove the publish_copies and alias fields from the form
        form.fields.pop("publish_copies")
        form.fields.pop("alias")

        # Check if user is submitting
        if request.method == "POST":
            # Prefill parent_page in case the form is invalid (as prepopulated value for the form field,
            # because ModelChoiceField seems to not fall back to the user given value)
            parent_page = Page.objects.get(id=request.POST["new_parent_page"])

            if form.is_valid():
                # Receive the parent page (this should never be empty)
                if form.cleaned_data["new_parent_page"]:
                    parent_page = form.cleaned_data["new_parent_page"]

                action = CopyPageAction(
                    page=page,
                    recursive=form.cleaned_data.get("copy_subpages"),
                    to=parent_page,
                    update_attrs={
                        "title": form.cleaned_data["new_title"],
                        "slug": form.cleaned_data["new_slug"],
                        "sent": timezone.localtime(),
                    },
                    keep_live=False,
                    copy_revisions=False,
                    user=request.user,
                )
                new_page = action.execute()

                # Add edit button to success message
                buttons = [messages.button(
                    reverse("wagtailadmin_pages:edit", args=(new_page.id,)),
                    _("Edit Copied Alert"),
                )]

                messages.success(
                    request,
                    _("Alert '%(page_title)s' copied.")
                    % {"page_title": page.specific_deferred.get_admin_display_title()},
                    buttons=buttons
                )

                for fn in hooks.get_hooks("after_copy_page"):
                    result = fn(request, page, new_page)
                    if hasattr(result, "status_code"):
                        return result

                # Redirect to the parent page
                return redirect("wagtailadmin_explore", parent_page.id)

        return TemplateResponse(
            request,
            "wagtailadmin/pages/copy.html",
            {
                "page": page,
                "form": form,
            },
        )

    return
