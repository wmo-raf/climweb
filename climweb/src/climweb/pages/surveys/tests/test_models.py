from wagtail.test.utils import WagtailPageTestCase

from climweb.pages.home.tests.factories import get_or_create_homepage
from .factories import SurveyPageFactory


class TestSurveyPage(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        cls.page = SurveyPageFactory(parent=home_page)
    
    def test_survey_page_render(self):
        self.assertPageIsRenderable(self.page)
