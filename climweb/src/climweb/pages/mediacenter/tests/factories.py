import factory
import wagtail_factories

from .. import models


class MediaIndexPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.MediaIndexPage
    
    title = "Media Center"
    banner_image = factory.SubFactory(wagtail_factories.ImageFactory)
    banner_title = "Media Center"
    introduction_title = "Our Media"
    introduction_text = "Welcome to our media center. Here you can find all of our media content."
