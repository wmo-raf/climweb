from wagtail.test.utils import WagtailPageTestCase

from climweb.pages.home.tests.factories import get_or_create_homepage
from .factories import (
    WeatherPageFactory,
    DailyWeatherReportIndexPageFactory,
    DailyWeatherReportDetailPageFactory
)


class TestWeatherPage(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        cls.page = WeatherPageFactory(parent=home_page)
    
    def test_root_render(self):
        self.assertPageIsRoutable(self.page)
    
    def test_sub_route_render(self):
        self.assertPageIsRoutable(self.page, route_path="daily-table/nairobi/")


class TestDailyWeatherReportIndexPage(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        cls.page = DailyWeatherReportIndexPageFactory(parent=home_page)
    
    def test_page_render(self):
        self.assertPageIsRenderable(self.page)


class TestDailyWeatherReportDetailPage(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        cls.page = DailyWeatherReportDetailPageFactory(parent=home_page)
    
    def test_page_render(self):
        self.assertPageIsRenderable(self.page)
