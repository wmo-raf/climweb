import factory
import wagtail_factories

from .. import models


class StaffPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.StaffPage
    
    title = "Staff"
    banner_title = "Our Staff"
    banner_image = factory.SubFactory(wagtail_factories.ImageFactory)
