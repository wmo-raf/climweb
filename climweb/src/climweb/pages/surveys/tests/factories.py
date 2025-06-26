import factory
import wagtail_factories

from .. import models


class SurveyPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.SurveyPage
    
    title = factory.sequence(lambda n: 'Survey %d' % n)
