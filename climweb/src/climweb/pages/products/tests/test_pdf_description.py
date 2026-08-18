"""
Tests for deriving a product description from a PDF's opening paragraph.

The value of this feature lives entirely in the heuristics: a bulletin begins
with a letterhead, a title in capitals and a date line, so "the first paragraph"
taken literally would put the issuing ministry's name on every product. These
tests pin down what gets skipped and what gets kept.
"""

from django.test import SimpleTestCase

from climweb.pages.products.tasks import (
    _extract_pdf_description,
    _first_paragraph_from_text,
    _looks_like_heading,
)


class LooksLikeHeadingTests(SimpleTestCase):
    def test_all_caps_lines_are_headings(self):
        self.assertTrue(_looks_like_heading("NATIONAL METEOROLOGICAL AGENCY"))
        self.assertTrue(_looks_like_heading("WEEKLY RAINFALL BULLETIN"))

    def test_date_and_reference_lines_are_headings(self):
        self.assertTrue(_looks_like_heading("2026-08-12 06:00 UTC"))
        self.assertTrue(_looks_like_heading(
            "Station 1: 45.2 mm  Station 2: 38.7 mm  Station 3: 12.9 mm  Station 4: 51.0 mm"
        ))

    def test_a_long_metadata_line_is_a_heading(self):
        # Long enough and prosaic enough to pass every length check, so only the
        # metadata signals keep it out of the description.
        self.assertTrue(_looks_like_heading(
            "Issued: 12 August 2026 at 06:00 UTC by the National Meteorological "
            "Agency, Reference NMA/WRB/2026/33, valid until 19 August 2026"
        ))
        self.assertTrue(_looks_like_heading(
            "Valid from 12 August 2026 to 19 August 2026 for all coastal districts"
        ))
        self.assertTrue(_looks_like_heading(
            "Prepared by: the Forecasting Division of the National Meteorological Agency"
        ))

    def test_ordinary_prose_is_not_a_heading(self):
        self.assertFalse(_looks_like_heading(
            "Rainfall during the past week was above average across much of "
            "the central highlands."
        ))

    def test_prose_that_quotes_figures_is_not_a_heading(self):
        # The point of the thresholds is to reject mastheads without rejecting
        # forecasts, which are full of measurements and dates.
        self.assertFalse(_looks_like_heading(
            "Totals exceeded 80 mm in 5 districts, while 3 stations recorded "
            "over 100 mm during the same period of observation."
        ))
        self.assertFalse(_looks_like_heading(
            "Heavy rainfall is expected to continue until 19 August across the "
            "northern districts, with totals of up to 60 mm in exposed areas."
        ))


class FirstParagraphTests(SimpleTestCase):
    BULLETIN = """MINISTRY OF TRANSPORT
NATIONAL METEOROLOGICAL AGENCY

WEEKLY RAINFALL BULLETIN

Issued: 12 August 2026
Ref: NMA/WRB/2026/33

Rainfall during the past week was above average across much of the central
highlands, with totals exceeding 80 mm in several districts. The heaviest
falls were recorded in the north west.

Farmers are advised to delay planting until conditions improve.
"""

    def test_skips_the_letterhead_and_takes_the_prose(self):
        result = _first_paragraph_from_text(self.BULLETIN)
        self.assertTrue(result.startswith("Rainfall during the past week"))
        self.assertNotIn("MINISTRY", result)
        self.assertNotIn("Ref:", result)

    def test_rejoins_lines_that_pdftotext_wrapped(self):
        # pdftotext preserves the page's visual line breaks; a paragraph must
        # come back as one line, not four.
        result = _first_paragraph_from_text(self.BULLETIN)
        self.assertNotIn("\n", result)
        self.assertIn("central highlands", result)

    def test_a_single_block_with_no_blank_lines_works(self):
        text = (
            "The seasonal forecast for September to November indicates a high "
            "probability of above normal rainfall across the eastern sector."
        )
        self.assertEqual(_first_paragraph_from_text(text), text)

    def test_empty_text_yields_nothing(self):
        # This is the normal result for a scanned bulletin.
        self.assertEqual(_first_paragraph_from_text(""), "")
        self.assertEqual(_first_paragraph_from_text(None), "")

    def test_a_title_only_page_yields_nothing(self):
        text = "NATIONAL WEATHER SERVICE\n\nDAILY FORECAST\n\n15 AUGUST 2026\n"
        self.assertEqual(_first_paragraph_from_text(text), "")

    def test_short_fragments_are_not_used(self):
        self.assertEqual(_first_paragraph_from_text("Page 1 of 4\n\nSee overleaf.\n"), "")

    def test_long_paragraphs_are_cut_at_a_sentence(self):
        sentence = "The ridge of high pressure persists over the region. "
        result = _first_paragraph_from_text(sentence * 20)
        self.assertLessEqual(len(result), 600)
        self.assertTrue(result.endswith("."))

    def test_a_long_paragraph_without_sentences_never_cuts_mid_word(self):
        result = _first_paragraph_from_text("rainfall " * 200)
        self.assertLessEqual(len(result), 601)
        self.assertFalse(result.rstrip("…").endswith("rainfal"))


class ExtractPdfDescriptionTests(SimpleTestCase):
    """The subprocess boundary: failure must never break ingestion."""

    def test_a_missing_file_returns_empty(self):
        self.assertEqual(_extract_pdf_description("/nonexistent/nope.pdf"), "")

    def test_a_file_that_is_not_a_pdf_returns_empty(self):
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".pdf") as handle:
            handle.write(b"this is not a pdf")
            handle.flush()
            self.assertEqual(_extract_pdf_description(handle.name), "")
