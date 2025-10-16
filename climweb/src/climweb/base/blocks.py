import uuid

from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.blocks import StructValue
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtailiconchooser.blocks import IconChooserBlock
from wagtailmodelchooser.blocks import ModelChooserBlock

from climweb.config.settings.base import SUMMARY_RICHTEXT_FEATURES, FULL_RICHTEXT_FRATURES
from .constants import LANGUAGE_CHOICES, LANGUAGE_CHOICES_DICT


class AbstractFormBlock(blocks.StructBlock):
    """
    Block class to be subclassed for blocks that involve form handling.
    """

    def get_result(self, page, request, value, is_submitted):
        handler_class = self.get_handler_class()
        handler = handler_class(page, request, block_value=value)
        return handler.process(is_submitted)

    def get_handler_class(self):
        handler_path = self.meta.handler
        if not handler_path:
            raise AttributeError(
                'You must set a handler attribute on the Meta class.')
        return import_string(handler_path)

    def is_submitted(self, request, sfname, index):
        form_id = 'form-%s-%d' % (sfname, index)
        if request.method.lower() == self.meta.method.lower():
            query_dict = getattr(request, self.meta.method.upper())
            return form_id in query_dict.get('form_id', '')
        return False

    class Meta:
        # This should be a dotted path to the handler class for the block.
        handler = None
        method = 'POST'
        icon = 'form'


class TitleTextImageBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=100, verbose_name=_('Section Title'),
                             help_text=_("Section Title"), )
    text = blocks.RichTextBlock(features=FULL_RICHTEXT_FRATURES, verbose_name=_('Section Text'),
                                help_text=_("Section description"))
    image = ImageChooserBlock(required=False)

    class Meta:
        template = "streams/title_text_image.html"
        icon = "placeholder"
        label = _("Title, Text and Image")


class TitleOnlyBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=100, verbose_name=_('Section Title'),
                             help_text=_("Section Title"), )
    
    class Meta:
        template = "streams/title_only.html"
        icon = "h1"
        label = _("Title")

class TextOnlyBlock(blocks.StructBlock):
    text = blocks.RichTextBlock(features=FULL_RICHTEXT_FRATURES, verbose_name=_('Section Text'),
                                help_text=_("Section description"))

    class Meta:
        template = "streams/text_only.html"
        icon = "bars"
        label = _("Text")

class TitleTextBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=100, verbose_name=_('Section Title'),
                             help_text=_("Section Title"), )
    text = blocks.RichTextBlock(features=FULL_RICHTEXT_FRATURES, verbose_name=_('Section Text'),
                                help_text=_("Section description"))

    class Meta:
        template = "streams/title_text.html"
        icon = "placeholder"
        label = _("Title and Text")


class FeatureBlock(blocks.StructBlock):
    FIGURE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('chart', 'Chart'),
        ('video', 'Video'),
        ('imageofchange', 'Image of Change')
    ]

    figure_type = blocks.ChoiceBlock(choices=FIGURE_TYPE_CHOICES)
    # image_of_change = blocks.PageChooserBlock(required=False, target_model='imagesofchange.ImageOfChangePage')
    image = ImageChooserBlock(required=False)
    chart_config_url = blocks.URLBlock(required=False, help_text=_("A URL that returns Highcharts.js configuration, "
                                                                   "including the data"))

    title = blocks.CharBlock()
    text = blocks.RichTextBlock(label=_("Description"), features=SUMMARY_RICHTEXT_FEATURES)
    action_link_text = blocks.CharBlock(max_length=15, required=False)
    action_link = blocks.PageChooserBlock(required=False, label=_("Action Link Internal"))
    action_link_external = blocks.URLBlock(required=False, max_length=400,
                                           help_text=_("An external link to a detailed resource on the internet."
                                                       "If provided, the internal link will be ignored"))

    class Meta:
        template = "streams/feature_block.html"
        icon = "placeholder"
        label = _("Feature Block")


class CollapsibleBlock(blocks.StructBlock):
    heading = blocks.CharBlock()
    description = blocks.RichTextBlock(features=SUMMARY_RICHTEXT_FEATURES)
    image = ImageChooserBlock(required=False)

    class Meta:
        template = "streams/collapsible_block.html"
        icon = "placeholder"
        label = _("Collapsible Block")


class AccordionBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True)
    collapsibles = blocks.StreamBlock([
        ('collapsibles', CollapsibleBlock())
    ])

    class Meta:
        template = "streams/accordion.html"
        icon = "placeholder"
        label = _("Accordion")


class TableInfoBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True)
    table = TableBlock(table_options={
        'colHeaders': False,
        'rowHeaders': False,
    })

    class Meta:
        template = "streams/table_block.html"


class SocialMediaBlock(blocks.StructBlock):
    name = blocks.CharBlock(max_length=60, )
    icon = IconChooserBlock(required=False, label=_("Icon"))
    full_url = blocks.URLBlock(max_length=255, help_text=_("The full url link that takes you to the page"))

    class Meta:
        icon = 'placeholder'
        label = _("Social Media Account")


class CollapsibleTextBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=255)
    description = blocks.RichTextBlock(features=SUMMARY_RICHTEXT_FEATURES)
    link_text = blocks.CharBlock(max_length=100, required=False)
    link_related_page = blocks.PageChooserBlock(required=False)

    class Meta:
        template = "streams/collapsible_text_block.html"
        icon = "placeholder"
        label = _("Collapsible Text Block")


class AdditionalMaterialBlock(blocks.StructBlock):
    MATERIAL_TYPE_CHOICES = (
        ("document", "Document/File"),
        ("image", "Image"),
    )
    type = blocks.ChoiceBlock(choices=MATERIAL_TYPE_CHOICES, required=True)
    title = blocks.CharBlock(max_length=255)
    document = DocumentChooserBlock(required=False, help_text=_("Select document or file"),
                                    verbose_name=_("Document/File"))
    image = ImageChooserBlock(required=False, help_text=_("Select/upload image"))

    class Meta:
        icon = "placeholder"
        label = _("Additional Material")


class CategorizedAdditionalMaterialBlock(blocks.StructBlock):
    category = blocks.CharBlock(max_length=255)
    materials = blocks.ListBlock(AdditionalMaterialBlock())

    class Meta:
        icon = "placeholder"
        label = _("Additional Materials")
        template = 'streams/categorized_materials_block.html'


class NavigationSubItemBlock(blocks.StructBlock):
    label = blocks.CharBlock(label=_("Label"))
    page = blocks.PageChooserBlock(required=False, label=_("Page"))
    external_url = blocks.URLBlock(required=False, label=_("External URL"))
    is_action = blocks.BooleanBlock(required=False, label=_("Show as action button"))


class NavigationItemStructValue(StructValue):
    def has_sub_items(self):
        sub_items = self.get("sub_items")
        page = self.get("page")
        include_subpages = self.get("include_subpages")
        if sub_items:
            return True
        if page and include_subpages and page.get_children():
            return True


class NavigationItemBlock(blocks.StructBlock):
    label = blocks.CharBlock(label=_("Label"))
    page = blocks.PageChooserBlock(required=False, label=_("Page"))
    external_url = blocks.URLBlock(required=False, label=_("External URL"))
    include_subpages = blocks.BooleanBlock(required=False, label=_("Include Subpages"))
    large_submenu = blocks.BooleanBlock(required=False, label=_("Large Submenu Dropdown"))
    sub_items = blocks.StreamBlock([
        ('sub_item', NavigationSubItemBlock())
    ], required=False)

    class Meta:
        template = "blocks/main_menu.html"
        icon = 'menu'
        value_class = NavigationItemStructValue


class FooterNavigationItemBlock(NavigationItemBlock):
    class Meta:
        template = "blocks/footer_menu.html"


class LanguageItemStructValue(StructValue):
    def lang_val(self):
        code = self.get("language")
        language = LANGUAGE_CHOICES_DICT.get(code)
        return language


class LanguageItemBlock(blocks.StructBlock):
    language = blocks.ChoiceBlock(max_length=20, choices=LANGUAGE_CHOICES)

    class Meta:
        value_class = LanguageItemStructValue


class UUIDModelChooserBlock(ModelChooserBlock):
    def get_form_state(self, value):
        data = self.widget.get_value_data(value)
        if data and data.get("id"):
            data["id"] = str(data["id"])
        return data

    def get_prep_value(self, value):
        # the native value (a model instance or None) should serialise to a PK or None
        if value is None:
            return None
        else:
            return str(value.pk)

    def to_python(self, value):
        # the incoming serialised value should be None or an ID
        if value is None:
            return value
        else:
            try:
                return self.model_class.objects.get(pk=uuid.UUID(value))
            except self.model_class.DoesNotExist:
                return None

    def bulk_to_python(self, values):
        objects = self.model_class.objects.in_bulk(values)
        return [
            objects.get(uuid.UUID(id)) for id in values
        ]
    
class WhatWeDoBlock(blocks.StructBlock):
    icon = IconChooserBlock(required=False, label=_("Icon"))
    title = blocks.CharBlock(max_length=60, required=False)
    description = blocks.RichTextBlock(features=SUMMARY_RICHTEXT_FEATURES)

    class Meta:
        template = 'streams/what_we_do_block.html'
        icon = 'placeholder'
        label = _("Card")


class WhatWeDoGroupBlock(blocks.StructBlock):
    what_we_do_items = blocks.ListBlock(WhatWeDoBlock())
    what_we_do_button_text = blocks.CharBlock(max_length=20, required=False, label=_("Card button text"))
    what_we_do_button_link = blocks.PageChooserBlock(required=False, label=_("Card button link"))

    class Meta:
        icon = "placeholder"
        label = _("Cards with Icon and Text")
        template = 'streams/what_we_do_group.html'