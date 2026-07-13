from wagtail.test.utils import WagtailPageTestCase

from climweb.base.seo_utils import get_html_meta_tags
from climweb.base.test_utils import test_page_meta_tags
from climweb.pages.home.tests.factories import get_or_create_homepage
from .factories import FlexibleFormPageFactory
from ..models import FlexibleFormPage


class TestFlexibleFormPage(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()

        cls.page = FlexibleFormPageFactory(parent=home_page)

    def test_default_route_rendering(self):
        self.assertPageIsRenderable(self.page)

    def test_meta_tags(self):
        resp = self.client.get(self.page.get_url())

        meta_tags = get_html_meta_tags(resp.content)

        test_page_meta_tags(self, self.page, meta_tags, request=resp.wsgi_request)

    def test_multiple_flexible_form_pages_can_be_created(self):
        # unlike the other built-in form pages (Contact, Feedback, Data Request), the
        # FlexibleFormPage has no max_count, so several instances can coexist under
        # the same parent.
        home_page = self.page.get_parent()

        second_page = FlexibleFormPageFactory(parent=home_page, title="Second Flexible Form")

        self.assertNotEqual(self.page.pk, second_page.pk)
        self.assertEqual(
            FlexibleFormPage.objects.descendant_of(home_page, inclusive=False).count(), 2
        )
