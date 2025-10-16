import factory
import wagtail_factories

from .. import models


class AviationPagePageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.AviationPage
    
    title = "Aviation"
