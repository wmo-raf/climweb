from wagtail.models import Page
from base.mixins import MetadataPageMixin

from wagtailsurveyjs.models import AbstractSurveyJsFormPage


class SurveyPage(MetadataPageMixin, AbstractSurveyJsFormPage):
    parent_page_types = ['home.HomePage']

    subpage_types = []
    template = "survey_form_page.html"

    content_panels = Page.content_panels
