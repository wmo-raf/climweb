import factory
import wagtail_factories
from wagtail.rich_text import RichText

from ..models import AnticipatoryActionPage


class AnticipatoryActionPageFactory(wagtail_factories.PageFactory):
    class Meta:
        model = AnticipatoryActionPage
    
    title = "Anticipatory Action"
    banner_image = factory.SubFactory(wagtail_factories.ImageFactory)
    banner_title = "Know the risk, act before the impact"
    hazard = "Drought"
    risk_level = "high"
    affected_areas = "North-eastern counties"
    risk_summary = RichText("<p>Below-average rainfall is expected over the coming season.</p>")
