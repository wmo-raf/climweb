"""
Static accessibility checks over ClimWeb's own templates, so regressions fail the test
suite. Rendered-page checks (contrast, landmarks, ARIA) live in tools/a11y/scan.py.
"""
import re
from pathlib import Path

from django.test import SimpleTestCase

CLIMWEB_ROOT = Path(__file__).resolve().parents[2]

# Wagtail admin and auth screens are Wagtail's own UI; the style guide is an internal reference page.
SKIP_PARTS = {"wagtailadmin", "admin", "two_factor", "wagtail_2fa", "axes", "modeladmin"}
SKIP_FILES = {"style_guide.html", "app_navbar.html"}

TAG_ATTRS = r"(?:[^>{]|\{[^}]*\})*"  # attributes, allowing {{ }} / {% %} inside them
IMG_RE = re.compile(r"<img\b" + TAG_ATTRS + r">", re.S)
CONTROL_RE = re.compile(r"<(a|button)\b(" + TAG_ATTRS + r")>(.*?)</\1>", re.S)
TABINDEX_RE = re.compile(r"\btabindex\s*=\s*[\"']?\s*([1-9]\d*)")


def public_templates():
    for path in sorted(CLIMWEB_ROOT.rglob("templates/**/*.html")):
        rel = path.relative_to(CLIMWEB_ROOT)
        if SKIP_PARTS.intersection(rel.parts) or path.name in SKIP_FILES:
            continue
        yield rel, path.read_text(errors="ignore")


def line_of(text, index):
    return text.count("\n", 0, index) + 1


def has_accessible_name(attrs, inner):
    if re.search(r"\baria-label(ledby)?\s*=", attrs):
        return True
    text = re.sub(r"<svg\b.*?</svg>|\{%\s*svg_icon[^%]*%\}|<!--.*?-->|\{#.*?#\}", "", inner, flags=re.S)
    if re.search(r'<img\b[^>]*\balt="[^"]+', text):
        return True
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\{%\s*(if|elif|else|endif|for|endfor|with|endwith|load|image)\b[^%]*%\}", "", text)
    return bool(re.sub(r"&[a-z]+;|&#\d+;", "", text).strip())


class TemplateAccessibilityTest(SimpleTestCase):
    def test_templates_found(self):
        self.assertGreater(len(list(public_templates())), 100)

    def test_every_img_has_alt(self):
        missing = [f"{rel}:{line_of(text, m.start())}"
                   for rel, text in public_templates()
                   for m in IMG_RE.finditer(text) if not re.search(r"\balt\s*=", m.group(0))]
        self.assertEqual(missing, [], "Add alt text (or alt=\"\" for decorative images) to these <img> tags")

    def test_no_positive_tabindex(self):
        found = [f"{rel}:{line_of(text, m.start())}"
                 for rel, text in public_templates() for m in TABINDEX_RE.finditer(text)]
        self.assertEqual(found, [], "Positive tabindex breaks the natural focus order; use 0 or -1")

    def test_icon_only_links_and_buttons_are_named(self):
        unnamed = []
        for rel, text in public_templates():
            for m in CONTROL_RE.finditer(text):
                tag, attrs, inner = m.groups()
                if re.search(r"<(a|button)\b", inner):
                    continue  # nested match; the inner control is checked on its own
                if tag == "a" and not re.search(r"\bhref\s*=", attrs):
                    continue  # not a link (e.g. loading skeletons)
                if re.search(r'aria-hidden="true"', attrs) and re.search(r'tabindex="-1"', attrs):
                    continue  # duplicate link hidden from keyboard and screen readers
                if not has_accessible_name(attrs, inner):
                    unnamed.append(f"{rel}:{line_of(text, m.start())}")
        self.assertEqual(unnamed, [], "Give these icon-only links/buttons an aria-label")

    def test_base_template_sets_language_and_skip_link(self):
        base = (CLIMWEB_ROOT / "config/templates/base.html").read_text()
        self.assertRegex(base, r"<html\s+lang=")
        self.assertIn('class="skip-link" href="#main-content"', base)
        self.assertIn('id="main-content"', base)
