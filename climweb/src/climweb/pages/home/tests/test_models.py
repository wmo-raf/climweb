from wagtail.test.utils import WagtailPageTestCase

from climweb.base.seo_utils import get_html_meta_tags
from climweb.base.test_utils import test_page_meta_tags
from .factories import get_or_create_homepage


class TestHomePage(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.page = get_or_create_homepage()
    
    def test_default_route_rendering(self):
        self.assertPageIsRenderable(self.page)
    
    def test_default_seo_image(self):
        self.assertEqual(self.page.get_meta_image(), self.page.hero_banner)
    
    def test_get_context_with_request(self):
        context = self.page.get_context(self.dummy_request)
        
        self.assertIn("country_bounds", context)
        self.assertIn("city_search_url", context)
        self.assertIn("home_map_settings_url", context)
        self.assertIn("home_weather_widget_url", context)
        
        if self.page.youtube_playlist:
            self.assertIn("youtube_playlist_url", context)
    
    def test_meta_tags(self):
        resp = self.client.get(self.page.full_url)
        
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.page, meta_tags, request=resp.wsgi_request)
