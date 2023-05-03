from django.utils.translation import gettext_lazy as _

from wagtail import blocks
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock


class TimelineBlock(blocks.StructBlock):
    year = blocks.CharBlock(max_length=5)

    milestones = blocks.ListBlock(
        blocks.StructBlock([
            ('period', blocks.CharBlock(max_length=50, required=False,
                                        help_text=_("This can be the month of the year or the exact date. "
                                                  "Leave blank if not known"))),
            ('description', blocks.TextBlock(help_text=_("Describe the milestone"), required=False))
        ]))

    class Meta:
        template = 'timeline_block.html'
        icon = 'placeholder'
        label = "Timeline"


class MaterialsDownloadBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=20)
    thumbnail = ImageChooserBlock()

    documents = blocks.ListBlock(
        blocks.StructBlock([
            ('title', blocks.CharBlock()),
            ('document', DocumentChooserBlock())
        ]))

    class Meta:
        template = 'materials_block.html'
        icon = 'placeholder'
        label = "Downloadable materials"