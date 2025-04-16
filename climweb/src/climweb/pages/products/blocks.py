from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.blocks import StructValue, StructBlockValidationError
from wagtail.contrib.table_block.blocks import TableBlock, DEFAULT_TABLE_OPTIONS
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtailiconchooser.blocks import IconChooserBlock


class ProductItemStructValue(StructValue):
    def product_item_type(self):
        from climweb.base.models import ProductItemType
        product_type = self.get('product_type')
        
        try:
            p = ProductItemType.objects.get(pk=product_type)
        except ObjectDoesNotExist:
            return None
        return p
    
    def product_date_str(self):
        return self.get("date").isoformat()
    
    @property
    def p_image(self):
        if self.get("image"):
            return self.get("image")
        if self.get("thumbnail"):
            return self.get("thumbnail")
        
        return None
    
    @property
    def description(self):
        return self.get("description")


class ProductItemTypeBlock(blocks.StructBlock):
    name = blocks.CharBlock(label=_("Name"))


class ProductCategoryBlock(blocks.StructBlock):
    name = blocks.CharBlock(label=_("Name"))
    icon = IconChooserBlock(label=_("Icon"))
    
    item_types = blocks.ListBlock(ProductItemTypeBlock())


class ProductItemImageContentBlock(blocks.StructBlock):
    product_type = blocks.CharBlock(required=True, label=_("Product Type"))
    date = blocks.DateBlock(required=True, label=_("Effective from"),
                            help_text=_("The date when this product becomes effective"))
    valid_until = blocks.DateBlock(required=False, label=_("Effective until"),
                                   help_text=_("The last day this product remains effective. "
                                               "Leave blank if not applicable"))
    image = ImageChooserBlock(required=True, label=_("Image"))
    description = blocks.RichTextBlock(required=False, label=_("Summary of the map/image information"))
    
    class Meta:
        value_class = ProductItemStructValue
    
    def clean(self, value):
        result = super().clean(value)
        valid_until = result.get('valid_until')
        
        if valid_until and valid_until < result['date']:
            raise StructBlockValidationError(block_errors={
                "valid_until": ValidationError(
                    _("The effective until date cannot be earlier than the effective from date"))
            })
        return result


class ProductItemDocumentContentBlock(blocks.StructBlock):
    product_type = blocks.CharBlock(required=True, label=_("Product Type"))
    date = blocks.DateBlock(required=True, label=_("Effective from"),
                            help_text=_("The date when this product becomes effective"))
    valid_until = blocks.DateBlock(required=False, label=_("Effective until"),
                                   help_text=_("The last day this product remains effective. "
                                               "Leave blank if not applicable"))
    document = DocumentChooserBlock(required=True, label=_("Document"))
    auto_generate_thumbnail = blocks.BooleanBlock(required=False, default=True,
                                                  label=_("Auto-generate thumbnail"),
                                                  help_text=_("If the document is a PDF, an image of the first page "
                                                              "will be auto-generated."))
    thumbnail = ImageChooserBlock(required=False, label=_("Thumbnail of the document"),
                                  help_text=_("For example a screen grab of the cover page. If left empty "
                                              "and Auto-generate above is checked and the uploaded document is a PDF, "
                                              "an image of the first page will be auto-generated."))
    description = blocks.RichTextBlock(required=False, label=_("Summary of the document information"))
    
    class Meta:
        value_class = ProductItemStructValue
    
    def clean(self, value):
        result = super().clean(value)
        valid_until = result.get('valid_until')
        
        if valid_until and valid_until < result['date']:
            raise StructBlockValidationError(block_errors={
                "valid_until": ValidationError(
                    _("The effective until date cannot be earlier than the effective from date"))
            })
        
        # generate thumbnail from document if not provided
        document = result.get('document')
        auto_generate_thumbnail = result.get('auto_generate_thumbnail')
        if document and auto_generate_thumbnail:
            thumbnail = document.get_thumbnail()
            if thumbnail:
                result["thumbnail"] = thumbnail
        return result


TABLE_OPTIONS = {
    "mergeCells": True,
    "contextMenu": DEFAULT_TABLE_OPTIONS["contextMenu"] + ["mergeCells"]
}


class ProductItemContentBlock(blocks.StreamBlock):
    table = TableBlock(table_options=TABLE_OPTIONS, label=_("Table"))
    text = blocks.RichTextBlock(label=_("Text"))


class ProductItemStreamContentBlock(blocks.StructBlock):
    product_type = blocks.CharBlock(required=True, label=_("Product Type"))
    date = blocks.DateBlock(required=True, label=_("Effective from"),
                            help_text=_("The date when this product becomes effective"))
    valid_until = blocks.DateBlock(required=False, label=_("Effective until"),
                                   help_text=_("The last day this product remains effective. "
                                               "Leave blank if not applicable"))
    content = ProductItemContentBlock(label=_("Content"))
    
    class Meta:
        value_class = ProductItemStructValue
    
    def clean(self, value):
        result = super().clean(value)
        valid_until = result.get('valid_until')
        
        if valid_until and valid_until < result['date']:
            raise StructBlockValidationError(block_errors={
                "valid_until": ValidationError(
                    _("The effective until date cannot be earlier than the effective from date"))
            })
        return result
