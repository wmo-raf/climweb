from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.blocks import StructValue
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtailiconchooser.blocks import IconChooserBlock

from base.constants import LANGUAGE_CHOICES, LANGUAGE_CHOICES_DICT
from nmhs_cms.settings.base import SUMMARY_RICHTEXT_FEATURES
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.contrib.typed_table_block.blocks import TypedTableBlock


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
                                          help_text=_("Section title"), )
    text = blocks.RichTextBlock(features=SUMMARY_RICHTEXT_FEATURES, verbose_name=_('Section Text'),
                                      help_text=_("Section description"))
    image =  ImageChooserBlock(required=False)

    class Meta:
        template = "streams/title_text_image.html"
        icon = "placeholder"
        label = "Title, Text and Image"

class TitleTextBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=100, verbose_name=_('Section Title'),
                                          help_text=_("Section title"), )
    text = blocks.RichTextBlock(features=SUMMARY_RICHTEXT_FEATURES, verbose_name=_('Section Text'),
                                      help_text=_("Section description"))

    class Meta:
        template = "streams/title_text.html"
        icon = "placeholder"
        label = "Title and Text"



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
    text = blocks.TextBlock(label=_("Description"))
    action_link_text = blocks.CharBlock(max_length=15, required=False)
    action_link = blocks.PageChooserBlock(required=False, label=_("Action Link Internal"))
    action_link_external = blocks.URLBlock(required=False, max_length=400,
                                           help_text=_("An external link to a detailed resource on the internet."
                                                       "If provided, the internal link will be ignored"))

    class Meta:
        template = "streams/feature_block.html"
        icon = "placeholder"
        label = "Feature Block"


class CollapsibleBlock(blocks.StructBlock):
    heading = blocks.CharBlock()
    description = blocks.RichTextBlock(features=SUMMARY_RICHTEXT_FEATURES)
    image = ImageChooserBlock(required=False)

    class Meta:
        template = "streams/collapsible_block.html"
        icon = "placeholder"
        label = "Collapsible Block"



class AccordionBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True)
    collapsibles = blocks.StreamBlock([
        ('collapsibles', CollapsibleBlock())
    ])

    class Meta:
        template = "streams/accordion.html"
        icon = "placeholder"
        label = "Accordion"


class TableInfoBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True)
    table = TableBlock(table_options={
        'colHeaders': False,
        'rowHeaders': False,
    })
    

    class Meta:
        template = "streams/table_block.html"


class WhatWeDoBlock(blocks.StructBlock):
    icon = IconChooserBlock(required=False,label=_("Icon"))
    title = blocks.CharBlock(max_length=60, required=False)
    description = blocks.CharBlock()

    class Meta:
        template = 'streams/what_we_do_block.html'
        icon = 'placeholder'
        label = "What we do"


class SocialMediaBlock(blocks.StructBlock):
    name = blocks.CharBlock(max_length=60, )
    icon = IconChooserBlock(required=False, label=_("Icon"))
    full_url = blocks.URLBlock(max_length=255, help_text=_("The full url link that takes you to the page"))

    class Meta:
        icon = 'placeholder'
        label = "Social Media Account"


class CollapsibleTextBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=255)
    description = blocks.RichTextBlock(features=SUMMARY_RICHTEXT_FEATURES)
    link_text = blocks.CharBlock(max_length=100, required=False)
    link_related_page = blocks.PageChooserBlock(required=False)

    class Meta:
        template = "streams/collapsible_text_block.html"
        icon = "placeholder"
        label = "Collapsible Text Block"


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
        label = "Additional Material"


class CategorizedAdditionalMaterialBlock(blocks.StructBlock):
    category = blocks.CharBlock(max_length=255)
    materials = blocks.ListBlock(AdditionalMaterialBlock())

    class Meta:
        icon = "placeholder"
        label = "Additional Materials"
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
    sub_items = blocks.ListBlock(NavigationSubItemBlock())

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
