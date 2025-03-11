import factory
import wagtail_factories

from .. import models


class DataRequestPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.DataRequestPage
    
    title = "Data Request"
    introduction_title = "Request For Data"
    introduction_subtitle = "Request for Data"
    illustration_image = factory.SubFactory(wagtail_factories.ImageFactory)
