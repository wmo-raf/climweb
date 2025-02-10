from wagtail.test.utils import WagtailPageTestCase

from climweb.base.seo_utils import get_html_meta_tags
from climweb.base.test_utils import test_page_meta_tags
from climweb.pages.home.tests.factories import get_or_create_homepage
from climweb.pages.organisation_pages.organisation.tests.factories import OrganisationIndexPageFactory
from .factories import TendersIndexPageFactory, TenderDetailPageFactory


class TestTenderPages(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        organisation_page = OrganisationIndexPageFactory(parent=home_page)
        cls.index_page = TendersIndexPageFactory(parent=organisation_page)
        
        cls.tender_page1 = TenderDetailPageFactory(parent=cls.index_page)
        cls.tender_page2 = TenderDetailPageFactory(parent=cls.index_page)
    
    def test_tenders_index_page_renderable(self):
        self.assertPageIsRenderable(self.index_page)
    
    def test_tenders_index_page_meta_tags(self):
        resp = self.client.get(self.index_page.get_url())
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.index_page, meta_tags)
    
    def test_tender_detail_page_renderable(self):
        self.assertPageIsRenderable(self.tender_page1)
        self.assertPageIsRenderable(self.tender_page2)
    
    def test_tender_detail_page_meta_tags(self):
        resp = self.client.get(self.tender_page1.get_url())
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.tender_page1, meta_tags)
        
        resp = self.client.get(self.tender_page2.get_url())
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.tender_page2, meta_tags)
