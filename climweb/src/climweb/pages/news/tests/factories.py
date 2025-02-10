import factory
import wagtail_factories
from wagtail.rich_text import RichText

from .. import models


class NewsIndexPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.NewsIndexPage
    
    title = "News"
    banner_image = factory.SubFactory(wagtail_factories.ImageChooserBlockFactory)
    banner_title = "Our News"
    banner_subtitle = "Stay up to date with our latest news"


class NewsTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.NewsType
    
    name = factory.Sequence(lambda n: "News Type {}".format(n))
    icon = factory.Faker("random_element", elements=["desktop", "comment", "date"])


class NewsPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.NewsPage
    
    title = factory.Sequence(lambda n: "News {}".format(n))
    date = factory.Faker("date_time_this_year", before_now=True, after_now=False)
    body = RichText("<p>News page body</p>")
    news_type = factory.SubFactory(NewsTypeFactory)
    
    @factory.post_generation
    def rich_text_field_with_image(self, create, extracted, **kwargs):
        if extracted:
            image = wagtail_factories.ImageChooserBlockFactory()
            image_tag = f'<embed alt="{image.title}" embedtype="image" format="fullwidth" id="{image.id}"/>'
            # self.body = RichText(f"<p>News page body</p>{image_tag}")
            # self.save()
