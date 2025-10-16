from datetime import timedelta

import factory
import wagtail_factories
from django.utils import timezone

from .. import models


class TendersIndexPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.TendersPage
    
    title = "Tenders"
    banner_title = "Our Tenders"
    banner_image = factory.SubFactory(wagtail_factories.ImageFactory)
    
    introduction_title = "Work with Us"
    introduction_text = factory.Faker('paragraph')
    introduction_image = factory.SubFactory(wagtail_factories.ImageFactory)


class TenderDetailPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.TenderDetailPage
    
    title = factory.Sequence(lambda n: f"Tender {n}")
    posting_date = factory.sequence(lambda n: timezone.now().replace(hour=0, minute=0, second=0) - timedelta(days=n))
    deadline = factory.sequence(lambda n: timezone.now().replace(hour=0, minute=0, second=0) + timedelta(days=n + 10))
    
    description = factory.Faker('paragraph')
    tender_document = factory.SubFactory(wagtail_factories.DocumentFactory)
