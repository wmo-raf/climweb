from wagtail import blocks


class ExternalLinkBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=255)
    link = blocks.URLBlock(max_length=255)

    class Meta:
        template = "external_link_block.html"
        icon = "placeholder"