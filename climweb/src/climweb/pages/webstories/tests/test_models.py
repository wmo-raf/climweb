from wagtail.test.utils import WagtailPageTestCase

from climweb.pages.home.tests.factories import get_or_create_homepage
from .factories import WebStoryListPageFactory


class TestWebStoriesPage(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        cls.list_page = WebStoryListPageFactory(parent=home_page)
    
    def test_list_page_render(self):
        self.assertPageIsRoutable(self.list_page)
