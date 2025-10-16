import factory
import wagtail_factories

from .. import models


class FlexPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.FlexPage
    
    title = "Flex Page"
    banner_image = factory.SubFactory(wagtail_factories.ImageFactory)
    banner_title = "Sample Flexible Page"
    banner_subtitle = "This is a sample flexible page"
