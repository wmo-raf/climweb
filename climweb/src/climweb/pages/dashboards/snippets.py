from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet

@register_snippet
class ChartSnippet(models.Model):
    CHART_TYPE_CHOICES = [
        ("line", "Line Chart"),
        ("bar", "Bar Chart"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    chart_type = models.CharField(max_length=10, choices=CHART_TYPE_CHOICES, default="line")
    dataset = models.ForeignKey(
        "geomanager.RasterFileLayer", on_delete=models.CASCADE, related_name="charts"
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("description"),
        FieldPanel("chart_type"),
        FieldPanel("dataset"),
    ]

    def __str__(self):
        return f"{self.dataset.title} ({self.chart_type} chart)"

    class Meta:
        verbose_name = "Dashboard Chart"
        verbose_name_plural = "Dashboard Charts"

@register_snippet
class DashboardMap(models.Model):

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    dataset = models.ForeignKey(
        "geomanager.RasterFileLayer", on_delete=models.CASCADE, related_name="maps"
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("description"),
        FieldPanel("dataset"),
    ]

    def __str__(self):
        return f"{self.dataset.title}"

    class Meta:
        verbose_name = "Dashboard Map"
        verbose_name_plural = "Dashboard Maps"