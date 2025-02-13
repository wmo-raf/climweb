import wagtail_factories

from .. import models


class SatelliteImagePageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.SatelliteImageryPage
    
    title = "Satellite Imagery"
