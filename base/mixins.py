from django.utils.translation import gettext_lazy
from wagtail.admin.panels import MultiFieldPanel, FieldPanel
from wagtail.admin.widgets.slug import SlugInput
from wagtailcache.cache import WagtailCacheMixin
from wagtailmetadata.models import MetadataPageMixin as BaseMetadataPageMixin


class MetadataPageMixin(BaseMetadataPageMixin, WagtailCacheMixin):
    class Meta:
        abstract = True

    promote_panels = [
        MultiFieldPanel(
            [
                FieldPanel("slug", widget=SlugInput),
                FieldPanel("seo_title"),
                FieldPanel('show_in_menus'),
                FieldPanel("search_description"),
                FieldPanel('search_image'),
            ],
            gettext_lazy("For search engines"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("show_in_menus"),
            ],
            gettext_lazy("For site menus"),
        ),
    ]
