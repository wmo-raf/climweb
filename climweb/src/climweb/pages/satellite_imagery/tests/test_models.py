from wagtail.test.utils import WagtailPageTestCase

from climweb.base.seo_utils import get_html_meta_tags
from climweb.base.test_utils import test_page_meta_tags
from climweb.pages.home.tests.factories import get_or_create_homepage
from .factories import SatelliteImagePageFactory


class TestSatelliteImageryPage(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        cls.page = SatelliteImagePageFactory(parent=home_page)
    
    def test_satellite_page_render(self):
        self.assertPageIsRenderable(self.page)
    
    def test_satellite_page_meta_tags(self):
        resp = self.client.get(self.page.get_url())
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.page, meta_tags, request=resp.wsgi_request)
