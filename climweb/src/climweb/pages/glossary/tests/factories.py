import factory
import wagtail_factories

from .. import models


class GlossaryIndexPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.GlossaryIndexPage
    
    title = "Glossary Index Page"
    introduction_image = factory.SubFactory(wagtail_factories.ImageFactory)
    introduction_title = "Glossary Index Introduction Title"
    introduction_text = "Glossary Index Introduction Text"


class GlossaryItemDetailPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.GlossaryItemDetailPage
    
    title = factory.Faker("word")
    brief_definition = factory.Faker("text")
