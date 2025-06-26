from datetime import timedelta

import factory
import wagtail_factories
from django.utils import timezone

from .. import models


class EventTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.EventType
    
    event_type = factory.Sequence(lambda n: "Event Type {}".format(n))
    icon = factory.Faker("random_element", elements=["desktop", "comment", "date"])


class EventIndexPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.EventIndexPage
    
    title = "Events"


class EventPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.EventPage
    
    title = factory.Sequence(lambda n: "Event {}".format(n))
    event_type = factory.SubFactory(EventTypeFactory)
    date_from = factory.sequence(lambda n: timezone.now().replace(hour=0, minute=0, second=0) + timedelta(days=n))
    timezone = "Africa/Nairobi"
    location = "Nairobi"
    description = factory.sequence(lambda n: "Description {}".format(n))


class EventRegistrationPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.EventRegistrationPage
    
    title = factory.Sequence(lambda n: "Event Registration {}".format(n))
