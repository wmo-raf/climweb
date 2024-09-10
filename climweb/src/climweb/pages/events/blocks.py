from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock

from climweb.config.settings.base import SUMMARY_RICHTEXT_FEATURES


class PanelistBlock(blocks.StructBlock):
    PANELIST_ROLE_CHOICES = (
        ("moderator", "Moderator"),
        ("discussant", "Discussant"),
    )
    name = blocks.CharBlock(max_length=255, help_text="Name of panelist")
    image = ImageChooserBlock(required=False, help_text="Select/upload image")
    organisation = blocks.CharBlock(max_length=255, required=False,
                                    help_text="Organisation working for or representing")
    position = blocks.CharBlock(max_length=255, required=False, help_text="Position in organisation")
    bio = blocks.RichTextBlock(required=False, help_text="Short bio", label="Short bio")
    role = blocks.ChoiceBlock(choices=PANELIST_ROLE_CHOICES, required=False,
                              help_text="Select Role. Leave blank if normal panelist")
    topic_title = blocks.CharBlock(max_length=255, required=False, help_text="Panelist's topic/session", )

    class Meta:
        icon = "placeholder"
        label = "Panelists"


class RoleBlock(blocks.StructBlock):
    ROLE_CHOICES = (
        ("moderator", "Moderator"),
        ("speaker", "Speaker"),
        ("rapporteur ", "Rapporteur"),
    )
    name = blocks.CharBlock(max_length=255, help_text="Name of person", label="Name of person")
    image = ImageChooserBlock(required=False, help_text="Select/upload image")
    role = blocks.ChoiceBlock(choices=ROLE_CHOICES, required=False, default="moderator", help_text="Select Role")


class SessionBlock(blocks.StructBlock):
    start_time = blocks.DateTimeBlock(help_text="Session Start Time")
    end_time = blocks.DateTimeBlock(help_text="Session End Time")
    image = ImageChooserBlock(required=False, help_text="Session Image")
    title = blocks.TextBlock(help_text="Session title")
    detail = blocks.RichTextBlock(required=False, help_text="Detail", features=SUMMARY_RICHTEXT_FEATURES)
    roles = blocks.ListBlock(RoleBlock())

    class Meta:
        icon = "placeholder"
        label = "Sessions"


class EventSponsorBlock(blocks.StructBlock):
    name = blocks.CharBlock(max_length=255, help_text="Name of sponsor")
    image = ImageChooserBlock(help_text="Select/upload image")
    link = blocks.URLBlock(required=False, help_text="Link to sponsor's page")
    enlarge = blocks.BooleanBlock(required=False, help_text="Enlarge image")

    class Meta:
        icon = "placeholder"
        label = "Acknowledgement"
