import factory
import wagtail_factories

from .. import models


class CityClimateDataPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.CityClimateDataPage
    
    title = factory.sequence(lambda n: 'City Climate %d' % n)
    description = factory.Faker('paragraph')
