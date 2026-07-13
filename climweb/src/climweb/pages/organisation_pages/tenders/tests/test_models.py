from datetime import timedelta

from django.utils import timezone
from wagtail.test.utils import WagtailPageTestCase

from climweb.base.seo_utils import get_html_meta_tags
from climweb.base.test_utils import test_page_meta_tags
from climweb.pages.flexible_forms.tests.factories import FlexibleFormPageFactory
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
        
        test_page_meta_tags(self, self.index_page, meta_tags, request=resp.wsgi_request)
    
    def test_tender_detail_page_renderable(self):
        self.assertPageIsRenderable(self.tender_page1)
        self.assertPageIsRenderable(self.tender_page2)
    
    def test_tender_detail_page_meta_tags(self):
        resp = self.client.get(self.tender_page1.get_url())
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.tender_page1, meta_tags, request=resp.wsgi_request)
        
        resp = self.client.get(self.tender_page2.get_url())
        meta_tags = get_html_meta_tags(resp.content)

        test_page_meta_tags(self, self.tender_page2, meta_tags, request=resp.wsgi_request)


class TestTenderDetailPageApply(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        organisation_page = OrganisationIndexPageFactory(parent=home_page)
        cls.index_page = TendersIndexPageFactory(parent=organisation_page)

        cls.application_page = FlexibleFormPageFactory(parent=home_page, title="Submit a Tender")

    def test_no_apply_url_when_nothing_configured(self):
        tender = TenderDetailPageFactory(parent=self.index_page)

        self.assertIsNone(tender.apply_url)

    def test_apply_url_uses_external_link_when_no_application_page(self):
        tender = TenderDetailPageFactory(
            parent=self.index_page,
            external_application_url="https://example.org/apply",
        )

        self.assertEqual(tender.apply_url, "https://example.org/apply")
        self.assertTrue(tender.apply_url_is_external)

    def test_apply_url_prefers_application_page_over_external_link(self):
        tender = TenderDetailPageFactory(
            parent=self.index_page,
            application_page=self.application_page,
            external_application_url="https://example.org/apply",
        )

        self.assertEqual(tender.apply_url, self.application_page.url)
        self.assertFalse(tender.apply_url_is_external)

    def test_apply_button_hidden_when_tender_is_closed(self):
        tender = TenderDetailPageFactory(
            parent=self.index_page,
            application_page=self.application_page,
            deadline=timezone.now() - timedelta(days=1),
        )

        resp = self.client.get(tender.get_url())

        self.assertNotContains(resp, "td-apply-btn")

    def test_apply_button_shown_when_tender_is_open(self):
        tender = TenderDetailPageFactory(
            parent=self.index_page,
            application_page=self.application_page,
        )

        resp = self.client.get(tender.get_url())

        self.assertContains(resp, "td-apply-btn")
