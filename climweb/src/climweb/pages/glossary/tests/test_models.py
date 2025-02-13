from wagtail.test.utils import WagtailPageTestCase

from climweb.base.seo_utils import get_html_meta_tags
from climweb.base.test_utils import test_page_meta_tags
from climweb.pages.home.tests.factories import get_or_create_homepage
from .factories import GlossaryIndexPageFactory, GlossaryItemDetailPageFactory


class TestGlossaryPages(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        
        cls.index_page = GlossaryIndexPageFactory(parent=home_page)
        cls.term1 = GlossaryItemDetailPageFactory(parent=cls.index_page)
        cls.term2 = GlossaryItemDetailPageFactory(parent=cls.index_page)
    
    def test_index_page_rendering(self):
        self.assertPageIsRenderable(self.index_page)
    
    def test_index_meta_tags(self):
        resp = self.client.get(self.index_page.get_url())
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.index_page, meta_tags, request=resp.wsgi_request)
    
    def test_term_pages_rendering(self):
        self.assertPageIsRenderable(self.term1)
        self.assertPageIsRenderable(self.term2)
    
    def test_term_pages_meta_tags(self):
        resp = self.client.get(self.term1.get_url())
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.term1, meta_tags, check_image=False, request=resp.wsgi_request)
        
        resp = self.client.get(self.term2.get_url())
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.term2, meta_tags, check_image=False, request=resp.wsgi_request)
