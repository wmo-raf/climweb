from wagtail.test.utils import WagtailPageTestCase

from climweb.pages.home.tests.factories import get_or_create_homepage
from .factories import CityClimateDataPageFactory


class TestCityClimateDataPage(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        cls.page = CityClimateDataPageFactory(parent=home_page)
    
    def test_page_render(self):
        self.assertPageIsRenderable(self.page)
