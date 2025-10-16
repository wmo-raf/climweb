import factory
import wagtail_factories

from .. import models


class FeedbackPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.FeedbackPage
    
    title = "Feedback"
    introduction_title = "Give Us Feedback"
    introduction_subtitle = "We value your feedback. Please let us know how we can improve our services."
    illustration = factory.SubFactory(wagtail_factories.ImageFactory)
