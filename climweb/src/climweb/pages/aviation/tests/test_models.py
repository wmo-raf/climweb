from wagtail.test.utils import WagtailPageTestCase

from climweb.pages.home.tests.factories import get_or_create_homepage
from .factories import AviationPagePageFactory


class TestAviationPage(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        cls.page = AviationPagePageFactory(parent=home_page)
    
    def test_page_render(self):
        self.assertPageIsRenderable(self.page)
