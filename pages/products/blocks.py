from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.blocks import StructValue
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtailiconchooser.blocks import IconChooserBlock


class ProductItemStructValue(StructValue):
    def product_item_type(self):
        from base.models import ProductItemType
        product_type = self.get('product_type')
        try:
            p = ProductItemType.objects.get(pk=product_type)
        except ObjectDoesNotExist:
            return None
        return p

    def p_image(self):
        if self.get("image"):
            return self.get("image")
        if self.get("thumbnail"):
            return self.get("thumbnail")


class ProductItemTypeBlock(blocks.StructBlock):
    name = blocks.CharBlock(label=_("Name"))


class ProductCategoryBlock(blocks.StructBlock):
    name = blocks.CharBlock(label=_("Name"))
    icon = IconChooserBlock(label=_("Icon"))

    item_types = blocks.ListBlock(ProductItemTypeBlock())


class ProductItemImageContentBlock(blocks.StructBlock):
    product_type = blocks.CharBlock(required=True, label=_("Product Type"))
    image = ImageChooserBlock(required=True, label=_("Image"))
    description = blocks.RichTextBlock(label=_("Summary of the map/image information"))

    class Meta:
        value_class = ProductItemStructValue


class ProductItemDocumentContentBlock(blocks.StructBlock):
    product_type = blocks.CharBlock(required=True, label=_("Product Type"))
    thumbnail = ImageChooserBlock(required=False, label=_("Thumbnail of the document"),
                                  help_text=_("For example a screen grab of the cover page"))
    document = DocumentChooserBlock(required=True, label=_("Document"))
    description = blocks.RichTextBlock(label=_("Summary of the document information"))

    class Meta:
        value_class = ProductItemStructValue
