from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.blocks import StructValue
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtailiconchooser.blocks import IconChooserBlock


class ProductItemStructValue(StructValue):
    def product_item_type(self):
        from core.models import ProductItemType
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
    product_type = blocks.CharBlock(required=True)
    image = ImageChooserBlock(required=True)
    description = blocks.RichTextBlock()

    class Meta:
        value_class = ProductItemStructValue


class ProductItemDocumentContentBlock(blocks.StructBlock):
    product_type = blocks.CharBlock(required=True)
    thumbnail = ImageChooserBlock(required=False)
    document = DocumentChooserBlock(required=True)
    description = blocks.RichTextBlock()

    class Meta:
        value_class = ProductItemStructValue
