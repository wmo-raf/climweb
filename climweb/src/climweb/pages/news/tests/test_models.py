import factory
import wagtail_factories
from wagtail.test.utils import WagtailPageTestCase

from climweb.pages.home.tests.factories import get_or_create_homepage
from .. import models


class NewsIndexPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.NewsIndexPage
    
    title = "News"
    banner_title = "Our News"
    banner_image = factory.SubFactory(wagtail_factories.ImageChooserBlockFactory)


class TestNewsIndexPage(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        cls.page = NewsIndexPageFactory(parent=home_page)
    
    def test_default_route(self):
        self.assertPageIsRenderable(self.page)
