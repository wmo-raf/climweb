from django.test import SimpleTestCase

from climweb.base.contrast import AA_TEXT, accessible_tint, contrast_ratio
from climweb.base.models import Theme
from climweb.base.templatetags.nmhs_cms_tags import severity_text_color
from climweb.base.utils import mix_with_white
from climweb.base.wagtail_hooks import theme_contrast_warnings


class TestContrastRatio(SimpleTestCase):
    def test_black_on_white_is_21(self):
        self.assertAlmostEqual(contrast_ratio("#000000", "#ffffff"), 21.0, places=2)

    def test_order_does_not_matter(self):
        self.assertEqual(contrast_ratio("#6b6b6b", "#ffffff"), contrast_ratio("#ffffff", "#6b6b6b"))

    def test_short_hex_is_accepted(self):
        self.assertEqual(contrast_ratio("#fff", "#000"), contrast_ratio("#ffffff", "#000000"))

    def test_muted_text_token_passes_on_white(self):
        self.assertGreaterEqual(contrast_ratio("#6b6b6b", "#ffffff"), AA_TEXT)


class TestAccessibleTint(SimpleTestCase):
    def test_keeps_80_percent_tint_when_it_already_passes(self):
        self.assertEqual(accessible_tint("#0c447c"), mix_with_white("#0c447c", 0.8))

    def test_lightens_tint_until_text_passes(self):
        # the theme default fails at 80% (4.31:1)
        self.assertLess(contrast_ratio("#176c9c", mix_with_white("#176c9c", 0.8)), AA_TEXT)
        self.assertGreaterEqual(contrast_ratio("#176c9c", accessible_tint("#176c9c")), AA_TEXT)

    def test_stops_for_colours_too_light_to_pass(self):
        # must return rather than loop forever
        self.assertTrue(accessible_tint("#f7d000").startswith("#"))


class TestThemeContrastWarnings(SimpleTestCase):
    def test_no_warnings_for_default_theme_colours(self):
        theme = Theme(primary_hover_color="#176c9c", primary_color="#363636")
        self.assertEqual(theme_contrast_warnings(theme), [])

    def test_warns_for_light_primary_colour(self):
        theme = Theme(primary_hover_color="#f7a600", primary_color="#363636")
        warnings = theme_contrast_warnings(theme)
        self.assertEqual(len(warnings), 1)
        self.assertIn("#f7a600", str(warnings[0]))

    def test_ignores_empty_colours(self):
        self.assertEqual(theme_contrast_warnings(Theme(primary_hover_color=None, primary_color=None)), [])


class TestSeverityTextColor(SimpleTestCase):
    def test_every_cap_severity_passes_on_its_background(self):
        # cap-composer's backgrounds for Extreme, Severe, Moderate, Minor, Unknown
        backgrounds = {4: "#FEE2E2", 3: "#FDE8D0", 2: "#FEF08A", 1: "#CFFAFE", 0: "#E0E7FF"}
        for severity_id, background in backgrounds.items():
            color = severity_text_color({"id": severity_id, "border_color": "#000000"})
            self.assertGreaterEqual(contrast_ratio(color, background), AA_TEXT, severity_id)
            self.assertGreaterEqual(contrast_ratio(color, "#ffffff"), AA_TEXT, severity_id)

    def test_falls_back_to_border_color_for_unknown_ids(self):
        self.assertEqual(severity_text_color({"id": 99, "border_color": "#123456"}), "#123456")

    def test_prefers_cap_composer_text_color(self):
        self.assertEqual(severity_text_color({"id": 4, "text_color": "#123456", "border_color": "#000000"}), "#123456")

    def test_empty_severity(self):
        self.assertEqual(severity_text_color(None), "")
