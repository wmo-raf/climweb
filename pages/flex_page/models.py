from django.db import models
from base.mixins import MetadataPageMixin
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail.admin.panels import FieldPanel,MultiFieldPanel
from wagtail.contrib.table_block.blocks import TableBlock
from base.models import AbstractBannerPage
from django.utils.translation import gettext_lazy as _
from base import  blocks

# model for flexible pages 
# Create your models here.
class FlexPage(AbstractBannerPage):
    template = "flex_page.html"

    parent_page_types = ['home.HomePage']

    content = StreamField(
        [
            ("title_text", blocks.TitleTextBlock()),
            ("title_text_image", blocks.TitleTextImageBlock()),
            ("accordion", blocks.AccordionBlock()),
            ("table", blocks.TableInfoBlock()),
            # ("table_type", blocks.TableType())

        ],
        null=True,
        blank=True,
        use_json_field=True
    )

    content_panels =  Page.content_panels + [
        *AbstractBannerPage.content_panels,
        FieldPanel("content")
        
    ]

    class Meta:
        verbose_name = _("Flex Page")

    

    
