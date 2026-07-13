from datetime import timedelta

from django.utils import timezone
from wagtail.test.utils import WagtailPageTestCase

from climweb.base.seo_utils import get_html_meta_tags
from climweb.base.test_utils import test_page_meta_tags
from climweb.pages.flexible_forms.tests.factories import FlexibleFormPageFactory
from climweb.pages.home.tests.factories import get_or_create_homepage
from climweb.pages.organisation_pages.organisation.tests.factories import OrganisationIndexPageFactory
from .factories import VacanciesIndexPageFactory, VacancyDetailPageFactory


class TestVacancyPages(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        organisation_page = OrganisationIndexPageFactory(parent=home_page)
        cls.index_page = VacanciesIndexPageFactory(parent=organisation_page)
        
        cls.vacancy_page1 = VacancyDetailPageFactory(parent=cls.index_page)
        cls.vacancy_page2 = VacancyDetailPageFactory(parent=cls.index_page)
    
    def test_vacancies_index_page_renderable(self):
        self.assertPageIsRenderable(self.index_page)
    
    def test_vacancies_index_page_meta_tags(self):
        resp = self.client.get(self.index_page.get_url())
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.index_page, meta_tags, request=resp.wsgi_request)
    
    def test_vacancy_detail_page_renderable(self):
        self.assertPageIsRenderable(self.vacancy_page1)
        self.assertPageIsRenderable(self.vacancy_page2)
    
    def test_vacancy_detail_page_meta_tags(self):
        resp = self.client.get(self.vacancy_page1.get_url())
        meta_tags = get_html_meta_tags(resp.content)
        
        test_page_meta_tags(self, self.vacancy_page1, meta_tags, request=resp.wsgi_request)
        
        resp = self.client.get(self.vacancy_page2.get_url())
        meta_tags = get_html_meta_tags(resp.content)

        test_page_meta_tags(self, self.vacancy_page2, meta_tags, request=resp.wsgi_request)


class TestVacancyDetailPageApply(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        organisation_page = OrganisationIndexPageFactory(parent=home_page)
        cls.index_page = VacanciesIndexPageFactory(parent=organisation_page)

        cls.application_page = FlexibleFormPageFactory(parent=home_page, title="Apply for a Job")

    def test_no_apply_url_when_nothing_configured(self):
        vacancy = VacancyDetailPageFactory(parent=self.index_page)

        self.assertIsNone(vacancy.apply_url)

    def test_apply_url_uses_external_link_when_no_application_page(self):
        vacancy = VacancyDetailPageFactory(
            parent=self.index_page,
            external_application_url="https://example.org/apply",
        )

        self.assertEqual(vacancy.apply_url, "https://example.org/apply")
        self.assertTrue(vacancy.apply_url_is_external)

    def test_apply_url_prefers_application_page_over_external_link(self):
        vacancy = VacancyDetailPageFactory(
            parent=self.index_page,
            application_page=self.application_page,
            external_application_url="https://example.org/apply",
        )

        self.assertEqual(vacancy.apply_url, self.application_page.url)
        self.assertFalse(vacancy.apply_url_is_external)

    def test_apply_button_hidden_when_vacancy_is_closed(self):
        vacancy = VacancyDetailPageFactory(
            parent=self.index_page,
            application_page=self.application_page,
            deadline=timezone.now() - timedelta(days=1),
        )

        resp = self.client.get(vacancy.get_url())

        self.assertNotContains(resp, "vd-apply-btn")

    def test_apply_button_shown_when_vacancy_is_open(self):
        vacancy = VacancyDetailPageFactory(
            parent=self.index_page,
            application_page=self.application_page,
        )

        resp = self.client.get(vacancy.get_url())

        self.assertContains(resp, "vd-apply-btn")
