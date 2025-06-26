from wagtail.test.utils import WagtailPageTestCase

from climweb.base.seo_utils import get_html_meta_tags
from climweb.base.test_utils import test_page_meta_tags
from climweb.pages.home.tests.factories import get_or_create_homepage
from .factories import PublicationsIndexPageFactory, PublicationPageFactory


class TestPublicationPages(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        cls.index_page = PublicationsIndexPageFactory(parent=home_page)
        
        cls.publication1_page = PublicationPageFactory(parent=cls.index_page)
        cls.publication2_page = PublicationPageFactory(parent=cls.index_page)
    
    def test_publication_index_page_render(self):
        self.assertPageIsRenderable(self.index_page)
    
    def test_publication_index_page_meta_tags(self):
        resp = self.client.get(self.index_page.get_url())
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.index_page, meta_tags, request=resp.wsgi_request)
    
    def test_publication_page_render(self):
        self.assertPageIsRenderable(self.publication1_page)
        self.assertPageIsRenderable(self.publication2_page)
    
    def test_publication_pages_meta_tags(self):
        resp = self.client.get(self.publication1_page.get_url())
        
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.publication1_page, meta_tags, request=resp.wsgi_request)
        
        resp = self.client.get(self.publication2_page.get_url())
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.publication2_page, meta_tags, request=resp.wsgi_request)
