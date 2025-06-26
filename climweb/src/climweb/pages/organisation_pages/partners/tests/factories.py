import factory
import wagtail_factories

from .. import models


class PartnerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Partner
    
    name = factory.Faker('company')
    logo = factory.SubFactory(wagtail_factories.ImageFactory)
    link = factory.Faker('url')
    order = factory.Sequence(lambda n: n)


class PartnerPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.PartnersPage
    
    title = "Partners"
    banner_title = "Our Partners"
    banner_image = factory.SubFactory(wagtail_factories.ImageFactory)
    
    introduction_title = "Join Us in Shaping the future"
    introduction_text = factory.Faker('paragraph')
