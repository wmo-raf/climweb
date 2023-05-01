from django.template.loader import render_to_string
from wagtail.admin.compare import ForeignObjectComparison
from wagtail.admin.panels import FieldPanel

from .widgets import AdminWebIconChooser


class WebIconChooserPanel(FieldPanel):
    object_type_name = "image"

    def widget_overrides(self):
        return {self.field_name: AdminWebIconChooser}

    def get_comparison_class(self):
        return WebIconFieldComparison


class WebIconFieldComparison(ForeignObjectComparison):
    def htmldiff(self):
        icon_a, icon_b = self.get_objects()

        return render_to_string("webicons/widgets/compare.html", {
            'icon_a': icon_a,
            'icon_b': icon_b,
        })
