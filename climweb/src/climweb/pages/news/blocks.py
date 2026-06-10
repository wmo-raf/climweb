from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from django.utils.translation import gettext_lazy as _


class ExternalLinkBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=255)
    link = blocks.URLBlock(max_length=255)

    class Meta:
        template = "external_link_block.html"
        icon = "placeholder"


class GalleryImageBlock(blocks.StructBlock):
    image = ImageChooserBlock(label=_("Image"))
    caption = blocks.CharBlock(
        required=False,
        max_length=255,
        label=_("Caption"),
        help_text=_("Optional caption or image source credit"),
    )

    class Meta:
        icon = "image"
        label = _("Image")


class MosaicImageGalleryBlock(blocks.StructBlock):
    title = blocks.CharBlock(
        required=False,
        max_length=255,
        label=_("Gallery title"),
        help_text=_("Optional heading displayed above the gallery"),
    )
    grid_style = blocks.ChoiceBlock(
        choices=[
            ("grid", _("Uniform Grid – all images same height")),
            ("masonry", _("Masonry – images keep natural proportions")),
        ],
        default="masonry",
        label=_("Layout style"),
    )
    columns = blocks.ChoiceBlock(
        choices=[
            ("2", _("2 columns")),
            ("3", _("3 columns")),
            ("4", _("4 columns")),
        ],
        default="3",
        label=_("Columns"),
    )
    images = blocks.ListBlock(GalleryImageBlock(), min_num=1, label=_("Images"))
    

    class Meta:
        template = "news/blocks/mosaic_gallery_block.html"
        icon = "image"
        label = _("Image Gallery")