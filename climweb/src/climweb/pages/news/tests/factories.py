import factory
import wagtail_factories

from .. import models


class NewsIndexPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.NewsIndexPage
    
    title = "News"
    banner_title = "Our News"
    banner_image = factory.SubFactory(wagtail_factories.ImageChooserBlockFactory)
