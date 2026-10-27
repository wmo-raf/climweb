from unittest import mock

from django.test import SimpleTestCase
from wagtail.blocks import StructBlockValidationError
from wagtail.images import get_image_model
from wagtail.images.blocks import ImageChooserBlock

from climweb.base.blocks import OptionalAltImageBlock
from climweb.base.templatetags.nmhs_cms_tags import image_alt


def make_image(title="IMG_2041.jpg", description=""):
    # collection_id avoids Wagtail looking up the root collection in the database
    return get_image_model()(title=title, description=description, width=10, height=10, collection_id=1)


class TestOptionalAltImageBlock(SimpleTestCase):
    def test_publishing_not_blocked_without_alt_text(self):
        block = OptionalAltImageBlock()
        image = make_image()
        image.contextual_alt_text = ""
        image.decorative = False
        with mock.patch.object(ImageChooserBlock, "clean", side_effect=lambda value: value):
            self.assertIs(block.clean(image), image)

    def test_image_itself_still_required_when_block_is_required(self):
        with self.assertRaises(StructBlockValidationError):
            OptionalAltImageBlock(required=True).clean(None)

    def test_legacy_id_does_not_use_title_as_alt_text(self):
        # data saved by ImageChooserBlock is a bare id; Wagtail would copy the title (a file name) into alt text
        image = make_image(title="Rotating_earth_(large)")
        with mock.patch.object(ImageChooserBlock, "to_python", return_value=image):
            value = OptionalAltImageBlock().to_python(42)
        self.assertEqual(value.contextual_alt_text, "")

    def test_legacy_id_keeps_image_description(self):
        image = make_image(description="Rainfall anomaly map for March")
        with mock.patch.object(ImageChooserBlock, "bulk_to_python", return_value=[image]):
            [value] = OptionalAltImageBlock().bulk_to_python([42])
        self.assertEqual(value.contextual_alt_text, "Rainfall anomaly map for March")


class TestImageAltTag(SimpleTestCase):
    def test_decorative_is_empty(self):
        image = make_image(description="A description")
        image.decorative = True
        image.contextual_alt_text = ""
        self.assertEqual(image_alt(image, "Heading"), "")

    def test_prefers_editor_alt_text_then_description_then_fallback(self):
        image = make_image(description="Image description")
        image.decorative = False
        image.contextual_alt_text = "Alt for this page"
        self.assertEqual(image_alt(image, "Heading"), "Alt for this page")

        image.contextual_alt_text = ""
        self.assertEqual(image_alt(image, "Heading"), "Image description")

        self.assertEqual(image_alt(make_image(), "Heading"), "Heading")

    def test_plain_image_and_missing_image(self):
        self.assertEqual(image_alt(make_image(description="Described"), "Heading"), "Described")
        self.assertEqual(image_alt(None, "Heading"), "Heading")
