from wagtail import blocks
from django.utils.translation import gettext_lazy as _


class ExtremeMeasurementBlock(blocks.StructBlock):
    station_name = blocks.CharBlock(required=True)
    value = blocks.FloatBlock(required=True)

    class Meta:
        template = 'weather/extremes_observation_block_item.html'


class ExtremeWeatherBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True, label=_("Weather Parameter"))
    units = blocks.CharBlock(required=False, label=_("Units"))
    measurements = blocks.StreamBlock([
        ('measurements', ExtremeMeasurementBlock(label=_("Measurement"))),
    ])

    class Meta:
        template = 'weather/extremes_observation_block.html'
