from wagtail.test.utils import WagtailPageTestCase

from climweb.pages.home.tests.factories import get_or_create_homepage
from .factories import StationsPageFactory


class TestStationPage(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        cls.page = StationsPageFactory(parent=home_page)
    
    def test_default_route(self):
        self.assertPageIsRoutable(self.page)
    
    def test_station_route(self):
        self.assertPageIsRoutable(self.page, route_path="10/")
        
        
