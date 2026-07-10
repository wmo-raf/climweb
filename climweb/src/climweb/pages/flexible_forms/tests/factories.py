import factory
import wagtail_factories

from .. import models


class FlexibleFormPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.FlexibleFormPage

    title = "Flexible Form"
    introduction_title = "Flexible Form"
    introduction_subtitle = "Tell us what you think"
    illustration_image = factory.SubFactory(wagtail_factories.ImageFactory)
