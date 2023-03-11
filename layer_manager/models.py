from django.db import models


from wagtail.models import Orderable, Page, ParentalKey, ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, FieldRowPanel
from wagtail.snippets.models import register_snippet


# Create your models here.
@register_snippet
class WMSRequest(ClusterableModel):

    OUTPUT_FORMATS = (
        ("image/png","PNG"),
        ("image/jpeg","JPEG"),
        ("image/svg+xml","SVG"),
        ("image/gif","GIF"),
    )

    title = models.CharField(max_length=250, null=False, blank=False, help_text="Title of your layer", verbose_name="Layer Title")
    subtitle = models.CharField(max_length=250, null=True, blank=True, help_text="Subtitle of your layer", verbose_name="Layer Subtitle")
    version = models.CharField(max_length=50, help_text="WMS Version", default="1.1.1", verbose_name="WMS Version")
    width = models.IntegerField(default=250, help_text="The size of the map image in pixels along the i axis", verbose_name="Pixel Width")
    height = models.IntegerField(default=250, help_text="The size of the map image in pixels along the j axis", verbose_name="Pixel Height")
    transparent = models.BooleanField(default=True, help_text="Ability of underlying maps to be visible or not", verbose_name="Transparency")
    srs = models.CharField(max_length=50, help_text="WMS Spatial Reference e.g EPSG:3857", default="EPSG:3857", verbose_name="Spatial Reference System")
    format = models.CharField(max_length=50,verbose_name="Output Format", help_text="Allowed map formats are either “picture” formats or “graphic element” formats. ", default="image/png", choices=OUTPUT_FORMATS) 
    legend = models.ForeignKey("Legend", on_delete=models.CASCADE, null=True)
    
    panels = [
        FieldPanel("title"),
        FieldPanel("subtitle"),
        FieldPanel("version"),
        FieldRowPanel([
            FieldPanel("width", classname="col6"),
            FieldPanel("height", classname="col6"),
        ]),
        FieldPanel("transparent"),
        FieldPanel("srs"),
        FieldPanel("format"),
        InlinePanel("layers", heading="WMS Layers", label="Layer" ),
        InlinePanel("styles", heading="Layer Styles", label="Layer Style"),
        InlinePanel("params", heading="Additional Parameters", label="Parameter"),
        FieldPanel("legend"),

    ]

    def __str__(self) -> str:
        return self.title

    class Meta:
        verbose_name = "WMS Request"
        verbose_name_plural = "WMS Requests"


class WMSStyle(Orderable):
    wms_request = ParentalKey(WMSRequest, verbose_name="WMS Styles", on_delete=models.CASCADE, related_name="styles")
    name = models.CharField(max_length=250, null=False, blank=False, help_text="The style's Name is used in the Map request STYLES parameter")


class Layer(Orderable):
    wms_request = ParentalKey(WMSRequest, verbose_name=("WMS Layers"), on_delete=models.CASCADE, related_name="layers")
    name = models.CharField(max_length=250, null=False, blank=False, help_text="WMS Layer is requested by using this name in the\
                                                                                LAYERS parameter of a GetMap request.")

class Param(Orderable):
    wms_request =  ParentalKey(WMSRequest, verbose_name=("Addtional Parameters"), on_delete=models.CASCADE, related_name="params")
    name = models.CharField(max_length=250, null=False, blank=False, help_text="Name of the parameter")
    value = models.CharField(max_length=250, null=False, blank=False, help_text="Value of the parameter")


@register_snippet
class Legend(ClusterableModel):

    LEGEND_TYPES =(
        ("basic","Basic"),
        ("gradient","Gradient"),
        ("cholorpleth","Cholorpleth"),
    )
    title = models.CharField(verbose_name=("Title"), max_length=50, help_text="Title of the Legend")
    legend_type = models.CharField(verbose_name=("Legend Type"), max_length=50, choices=LEGEND_TYPES, default="basic")

    panels = [
        FieldPanel("title"),
        FieldPanel("legend_type"),
        InlinePanel("legend_items", heading="Legend Items", label="Legend Item"),

    ]

    def __str__(self) -> str:
        return f"{self.title} - {self.legend_type}"



class LegendItem(Orderable):
    legend = ParentalKey(Legend, verbose_name=("Legend Items"), on_delete=models.CASCADE, related_name="legend_items", null=True)
    item_val = models.CharField(verbose_name=("Value"), max_length=50, help_text="Can be a number or text e.g '10' or '10-20' or 'Vegetation'")
    item_color = models.CharField(verbose_name=("Color"), max_length=50, help_text="Color denoting the value e.g rgb(73,73,73) or #494949")






    

