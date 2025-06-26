from wagtail.test.utils import WagtailPageTestCase

from climweb.base.seo_utils import get_html_meta_tags
from climweb.base.test_utils import test_page_meta_tags
from climweb.pages.home.tests.factories import get_or_create_homepage
from .factories import (
    EventIndexPageFactory,
    EventPageFactory,
    EventRegistrationPageFactory
)


class TestEventPages(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        cls.page = EventIndexPageFactory(parent=home_page)
        
        cls.event1 = EventPageFactory(parent=cls.page)
        cls.event2 = EventPageFactory(parent=cls.page)
        
        cls.event1_reg = EventRegistrationPageFactory(parent=cls.event1)
    
    def test_index_page_rendering(self):
        self.assertPageIsRenderable(self.page)
    
    def test_index_page_meta_tags(self):
        resp = self.client.get(self.page.get_url())
        
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.page, meta_tags, request=resp.wsgi_request)
    
    def test_event_page_rendering(self):
        self.assertPageIsRenderable(self.event1)
        self.assertPageIsRenderable(self.event2)
    
    def test_event_page_meta_tags(self):
        resp = self.client.get(self.event1.get_url())
        meta_tags = get_html_meta_tags(resp.content)
        test_page_meta_tags(self, self.event1, meta_tags, request=resp.wsgi_request)
    
    def test_event_registration_page_rendering(self):
        self.assertPageIsRenderable(self.event1_reg)
    
    def test_event_registration_page_meta_tags(self):
        resp = self.client.get(self.event1_reg.get_url())
        meta_tags = get_html_meta_tags(resp.content)
        test_page_meta_tags(self, self.event1_reg, meta_tags, request=resp.wsgi_request)
