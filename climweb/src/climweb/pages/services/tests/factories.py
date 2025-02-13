import factory
import wagtail_factories
from faker import Faker
from wagtail.rich_text import RichText

from climweb.base.models import ServiceCategory
from ..models import ServiceIndexPage, ServicePage

fake = Faker()


class ServiceCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ServiceCategory
    
    name = factory.Sequence(lambda n: f"Service {n}")
    icon = factory.Faker("random_element", elements=["desktop", "comment", "date"])


class ServiceIndexPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = ServiceIndexPage
    
    title = "Services"


class ServicePageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = ServicePage
    
    title = factory.sequence(lambda n: f"Service {n}")
    banner_image = factory.SubFactory(wagtail_factories.ImageFactory)
    banner_title = factory.Faker("sentence")
    
    introduction_title = factory.Faker("sentence")
    introduction_image = factory.SubFactory(wagtail_factories.ImageFactory)
    service = factory.SubFactory(ServiceCategoryFactory)
    
    @factory.lazy_attribute
    def introduction_text(self):
        p = fake.paragraph()
        return RichText(f"<p>{p}</p>")
