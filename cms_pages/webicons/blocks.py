from django.template.loader import render_to_string
from django.utils.functional import cached_property
from wagtail.admin.compare import BlockComparison
from wagtail.blocks import ChooserBlock

from cms_pages.webicons.models import WebIcon


class WebIconChooserBlock(ChooserBlock):
    @cached_property
    def target_model(self):
        return WebIcon

    @cached_property
    def widget(self):
        from cms_pages.webicons.widgets import AdminWebIconChooser
        return AdminWebIconChooser

    def render_basic(self, value, context=None):
        if value:
            return "<figure style='max-height:100px;max-width:100px'>" \
                   "<img src='{}' alt='{}' style='height:100%;width:100%;object-fit:contain'/></figure>". \
                format(value.url, value.title)
        else:
            return ''

    def get_comparison_class(self):
        return WebIconChooserBlockComparison

    class Meta:
        icon = "image"


class WebIconChooserBlockComparison(BlockComparison):
    def htmlvalue(self, val):
        return render_to_string("webicons/widgets/compare.html", {
            'icon_a': val,
            'icon_b': val,
        })

    def htmldiff(self):
        return render_to_string("webicons/widgets/compare.html", {
            'icon_a': self.val_a,
            'icon_b': self.val_b,
        })
