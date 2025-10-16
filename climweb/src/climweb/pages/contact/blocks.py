from django.utils.safestring import mark_safe
from wagtail import blocks

from climweb.config.settings.base import SUMMARY_RICHTEXT_FEATURES


class ContactDetailBlock(blocks.StructBlock):
    fa_icon = blocks.CharBlock(max_length=20, required=False, help_text=mark_safe(
        "Font Awesome icon without the leading fas or fab. E.g for Envelope icon, fa-envelope. Check "
        "the correct icon at "
        "<a target='_blank' href='https://fontawesome.com/icons?c=communication&m=free'>"
        "Font Awesome</a>. Type in on the search bar on that page to filter."))
    contact_type = blocks.CharBlock(max_length=255)
    contact_detail = blocks.RichTextBlock(features=SUMMARY_RICHTEXT_FEATURES)

    class Meta:
        icon = 'mail'
