from wagtail.test.utils import WagtailPageTestCase

from climweb.base.seo_utils import get_html_meta_tags
from climweb.base.test_utils import test_page_meta_tags
from climweb.pages.home.tests.factories import get_or_create_homepage
from .factories import NewsIndexPageFactory, NewsPageFactory


class TestNewsPages(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        cls.index_page = NewsIndexPageFactory(parent=home_page)
        cls.news1 = NewsPageFactory(parent=cls.index_page)
        cls.news2 = NewsPageFactory(parent=cls.index_page, rich_text_field_with_image=True)
    
    def test_index_page_render(self):
        self.assertPageIsRenderable(self.index_page)
    
    def test_index_page_meta_tags(self):
        resp = self.client.get(self.index_page.get_url())
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.index_page, meta_tags, request=resp.wsgi_request)
    
    def test_news_page_render(self):
        self.assertPageIsRenderable(self.news1)
        self.assertPageIsRenderable(self.news2)
    
    def test_news_page_meta_tags(self):
        resp = self.client.get(self.news1.get_url())
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.news1, meta_tags, check_image=False, request=resp.wsgi_request)
        
        resp = self.client.get(self.news2.get_url())
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.news2, meta_tags, check_image=False, request=resp.wsgi_request)
