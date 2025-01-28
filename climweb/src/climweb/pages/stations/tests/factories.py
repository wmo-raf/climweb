import wagtail_factories

from .. import models


class StationsPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.StationsPage
    
    title = "Stations"
