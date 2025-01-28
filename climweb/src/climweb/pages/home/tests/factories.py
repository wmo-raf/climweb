import factory
import wagtail_factories
from wagtail.models import Site

from .. import models


class HomePageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.HomePage
    
    title = "Home Page"
    hero_title = "National Meteorological and Hydrological Service"
    hero_subtitle = "Delivering climate services"
    hero_banner = factory.SubFactory(wagtail_factories.ImageChooserBlockFactory)


def get_or_create_homepage():
    home_page = models.HomePage.objects.first()
    if not home_page:
        site = Site.objects.get(is_default_site=True)
        home_page = HomePageFactory()
        site.root_page = home_page
        site.save()
    return home_page
