from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.blocks import StructValue
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock

from nmhs_cms.settings.base import SUMMARY_RICHTEXT_FEATURES


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


class WhatWeDoBlock(blocks.StructBlock):
    icon = blocks.CharBlock(required=False)
    title = blocks.CharBlock(max_length=60, required=False)
    description = blocks.CharBlock()

    class Meta:
        template = 'streams/what_we_do_block.html'
        icon = 'placeholder'
        label = "What we do"


class SocialMediaBlock(blocks.StructBlock):
    name = blocks.CharBlock(max_length=60, )
    fa_icon = blocks.CharBlock(max_length=60, verbose_name="Font Awesome icon",
                               help_text=mark_safe(
                                   "Font Awesome icon without the leading fab. E.g for Facebook, fa-facebook-f. Check "
                                   "the correct icon at "
                                   "<a target='_blank' href='https://fontawesome.com/icons?s=brands&m=free'>"
                                   "Font Awesome</a>. Type in on the search bar on that page to filter."))
    full_url = blocks.URLBlock(max_length=255, help_text=_("The full url link that takes you to the page"))
    user_id = blocks.CharBlock(max_length=100, required=False,
                               help_text=_("The user id if available, For example the user Id/"
                                           "name for twitter, Instagram or channel id for Youtube etc"))

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
        template = "blocks/menu.html"
        icon = 'menu'
        value_class = NavigationItemStructValue
