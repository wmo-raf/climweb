from datetime import timedelta

import factory
import wagtail_factories
from django.utils import timezone

from .. import models


class VacanciesIndexPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.VacanciesPage
    
    title = "Vacancies"
    banner_title = "Vacancies"
    banner_image = factory.SubFactory(wagtail_factories.ImageFactory)
    
    introduction_title = "Work with Us"
    introduction_text = factory.Faker('paragraph')
    introduction_image = factory.SubFactory(wagtail_factories.ImageFactory)


class VacancyDetailPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.VacancyDetailPage
    
    title = factory.Sequence(lambda n: f"Vacancy {n}")
    posting_date = factory.sequence(lambda n: timezone.now().replace(hour=0, minute=0, second=0) - timedelta(days=n))
    deadline = factory.sequence(lambda n: timezone.now().replace(hour=0, minute=0, second=0) + timedelta(days=n + 10))
    duty_station = factory.Faker('city')
    
    description = factory.Faker('paragraph')
    document = factory.SubFactory(wagtail_factories.DocumentFactory)
