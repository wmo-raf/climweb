from django.utils.translation import gettext_lazy as _
from wagtail_modeladmin.menus import ModelAdminMenuItem
from wagtail_modeladmin.options import modeladmin_register
from wagtailsurveyjs.wagtail_hooks import BaseSurveyModelAdmin

from .models import SurveyPage


class SurveyModelAdminMenuItem(ModelAdminMenuItem):
    def is_shown(self, request):
        return request.user.has_perm("base.can_view_survey_menu")


class SurveyModelAdmin(BaseSurveyModelAdmin):
    model = SurveyPage
    menu_label = _('Surveys')
    menu_icon = 'folder-inverse'
    menu_order = 600

    def get_menu_item(self, order=None):
        return SurveyModelAdminMenuItem(self, order or self.get_menu_order())


modeladmin_register(SurveyModelAdmin)
