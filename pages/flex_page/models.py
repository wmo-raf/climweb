from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page

from base import blocks
from base.models import AbstractBannerPage


# model for flexible pages
class FlexPage(AbstractBannerPage):
    template = "flex_page.html"

    parent_page_types = ['home.HomePage']

    content = StreamField(
        [
            ("title_text", blocks.TitleTextBlock()),
            ("title_text_image", blocks.TitleTextImageBlock()),
            ("accordion", blocks.AccordionBlock()),
            ("table", blocks.TableInfoBlock()),

        ],
        null=True,
        blank=True,
        use_json_field=True
    )

    content_panels = Page.content_panels + [
        *AbstractBannerPage.content_panels,
        FieldPanel("content")

    ]

    class Meta:
        verbose_name = _("Flex Page")
