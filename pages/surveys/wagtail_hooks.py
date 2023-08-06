from wagtail_modeladmin.options import modeladmin_register
from .models import SurveyPage  # your survejs page model
from wagtailsurveyjs.wagtail_hooks import BaseSurveyModelAdmin
from django.utils.translation import gettext_lazy as _


class SurveyModelAdmin(BaseSurveyModelAdmin):
    model = SurveyPage
    menu_label = _('Surveys')
    menu_icon = 'folder-inverse'
    menu_order = 600


modeladmin_register(SurveyModelAdmin)