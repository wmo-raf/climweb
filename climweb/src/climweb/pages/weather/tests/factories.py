import factory
import wagtail_factories
from wagtail.rich_text import RichText

from .. import models
from faker import Faker

fake = Faker()


class WeatherPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.WeatherDetailPage
    
    title = "Weather"


class DailyWeatherReportIndexPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.DailyWeatherReportIndexPage
    
    title = "Daily Weather Report"
    introduction_title = "Our daily weather report"
    introduction_image = factory.SubFactory(wagtail_factories.ImageFactory)
    
    @factory.lazy_attribute
    def introduction_text(self):
        p = fake.paragraph()
        
        return RichText(f"<p>{p}</p>")


class DailyWeatherReportDetailPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = models.DailyWeatherReportDetailPage
    
    issued_on = factory.Faker("date_this_year", before_today=True, after_today=False)
