import factory
import wagtail_factories
from faker import Faker
from wagtail.rich_text import RichText

from .. import models
from ...services.tests.factories import ServiceCategoryFactory

fake = Faker()


class PublicationTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PublicationType
    
    name = factory.Faker('word')
    icon = factory.Faker("random_element", elements=["desktop", "comment", "date"])


class PublicationsIndexPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.PublicationsIndexPage
    
    title = "Publications"
    banner_image = factory.SubFactory(wagtail_factories.ImageFactory)
    banner_title = "Publications"
    banner_subtitle = "Explore our publications"


class PublicationPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.PublicationPage
    
    title = factory.sequence(lambda n: f"Publication {n}")
    publication_type = factory.SubFactory(PublicationTypeFactory)
    publication_date = factory.Faker("date_this_year", before_today=True, after_today=False)
    thumbnail = factory.SubFactory(wagtail_factories.ImageFactory)
    document = factory.SubFactory(wagtail_factories.DocumentFactory)
    
    @factory.lazy_attribute
    def summary(self):
        p = fake.paragraph()
        return RichText(f"<p>{p}</p>")
    
    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return
        
        if extracted:
            for child in extracted:
                self.categories.add(child)
        else:
            # Create a default set of inline children
            service = ServiceCategoryFactory.create()
            self.categories.add(service)
        
        self.save()
