from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.blocks import StructValue, StructBlockValidationError
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtailiconchooser.blocks import IconChooserBlock
from wagtail.contrib.table_block.blocks import TableBlock, DEFAULT_TABLE_OPTIONS

from base.utils import get_first_page_of_pdf_as_image


class ProductItemStructValue(StructValue):
    def product_item_type(self):
        from base.models import ProductItemType
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
    thumbnail = ImageChooserBlock(required=False, label=_("Thumbnail of the document"),
                                  help_text=_("For example a screen grab of the cover page"))
    date = blocks.DateBlock(required=True, label=_("Effective from"),
                            help_text=_("The date when this product becomes effective"))
    valid_until = blocks.DateBlock(required=False, label=_("Effective until"),
                                   help_text=_("The last day this product remains effective. "
                                               "Leave blank if not applicable"))
    document = DocumentChooserBlock(required=True, label=_("Document"))
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
        thumbnail = result.get('thumbnail')
        if not thumbnail:
            document = result.get('document')
            # check if document extension is .pdf
            if document and document.file.name.endswith('.pdf'):
                document_title = document.title
                try:
                    current_time = timezone.localtime(timezone.now()).strftime("%Y-%m-%d-%H-%M-%S")
                    file_name = f"f{slugify(document_title)}-{current_time}-thumbnail.jpg"
                    thumbnail = get_first_page_of_pdf_as_image(document.file.path, title=document_title,
                                                               file_name=file_name)
                    if thumbnail:
                        result["thumbnail"] = thumbnail
                except:
                    # do nothing if thumbnail generation fails
                    pass

        return result


TABLE_OPTIONS = {
    "mergeCells": True,
    "contextMenu": DEFAULT_TABLE_OPTIONS["contextMenu"] + ["mergeCells"]
}


class ProductItemStreamContentBlock(blocks.StructBlock):
    product_type = blocks.CharBlock(required=True, label=_("Product Type"))
    date = blocks.DateBlock(required=True, label=_("Effective from"),
                            help_text=_("The date when this product becomes effective"))
    valid_until = blocks.DateBlock(required=False, label=_("Effective until"),
                                   help_text=_("The last day this product remains effective. "
                                               "Leave blank if not applicable"))
    content = blocks.StreamBlock([
        ('table', TableBlock(table_options=TABLE_OPTIONS, label=_("Table"))),
        ('text', blocks.RichTextBlock(label=_("Text")))
    ], label=_("Content"))

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
