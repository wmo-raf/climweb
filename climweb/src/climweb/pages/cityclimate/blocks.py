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
        orientation = self.get("orientation")
        if orientation == "vertical":
            chart_type = "column"
        else:
            chart_type = "bar"
        return {
            "type": chart_type,
            "color": self.get("fill_color")
        }


class BarChartBlock(blocks.StructBlock):
    orientation = blocks.ChoiceBlock(choices=(
        ('vertical', 'Vertical'),
        ('horizontal', 'Horizontal'),
    ), default="vertical")
    fill_color = NativeColorBlock(default="#2caffe", label=_("Fill Color"))

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
