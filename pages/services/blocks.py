from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtailiconchooser.blocks import IconChooserBlock

from nmhs_cms.settings.base import SUMMARY_RICHTEXT_FEATURES


class WhatWeDoBlock(blocks.StructBlock):
    icon = IconChooserBlock(required=False, label=_("Icon"))
    title = blocks.CharBlock(max_length=60, required=False)
    description = blocks.RichTextBlock(features=SUMMARY_RICHTEXT_FEATURES)

    class Meta:
        icon = 'placeholder'
        label = _("What we do")
