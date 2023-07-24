from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.blocks import StructValue
from wagtail_color_panel.blocks import NativeColorBlock


class LineChartStructValue(StructValue):
    @property
    def config(self):
        return {
            "type": "line",
            "color": self.get("line_color")
        }


class LineChartBlock(blocks.StructBlock):
    line_color = NativeColorBlock(default="#2caffe", label=_("Line Color"))

    class Meta:
        value_class = LineChartStructValue


class BarChartStructValue(StructValue):
    @property
    def config(self):
        return {
            "type": "bar",
            "color": self.get("fill_color")
        }


class BarChartBlock(blocks.StructBlock):
    fill_color = NativeColorBlock(default="#2caffe", label=_("Bar Fill Color"))

    class Meta:
        value_class = BarChartStructValue


class AreaChartStructValue(StructValue):
    @property
    def config(self):
        return {
            "type": "area",
            "color": self.get("fill_color")
        }


class AreaChartBlock(blocks.StructBlock):
    fill_color = NativeColorBlock(default="#2caffe", label=_("Area Fill Color"))

    class Meta:
        value_class = AreaChartStructValue
