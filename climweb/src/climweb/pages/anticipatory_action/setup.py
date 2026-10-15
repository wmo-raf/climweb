"""
Creating the Anticipatory Action page from a template, so editors start from a draft with example content
they replace rather than a blank form. Used when adding the page in the admin and by the
create_anticipatory_action_page command.
"""
from pathlib import Path

from django.core.files.images import ImageFile
from django.utils import timezone
from django.utils.translation import gettext as _
from wagtail.images import get_image_model
from wagtail.rich_text import RichText

from climweb.base.models import ImportantPages
from climweb.pages.home.models import HomePage
from .models import AnticipatoryActionPage

DEFAULT_SLUG = "anticipatory-action"

SAMPLE_BANNER_PATH = Path(__file__).parent / "setup_assets" / "sample_banner.jpg"
SAMPLE_BANNER_TITLE = "Anticipatory Action sample banner"


def get_existing_page():
    # max_count is 1, so there is at most one
    return AnticipatoryActionPage.objects.first()


def get_home_page(site):
    root_page = site.root_page.specific
    if not isinstance(root_page, HomePage):
        return None
    return root_page


def get_available_slug(parent, slug=DEFAULT_SLUG):
    """
    The slug, or the slug with a number appended if a sibling already uses it,
    e.g. when an existing Flex Page is already published at /anticipatory-action/
    """
    taken = set(parent.get_children().values_list("slug", flat=True))
    candidate = slug
    suffix = 2
    while candidate in taken:
        candidate = f"{slug}-{suffix}"
        suffix += 1
    return candidate


def get_or_create_sample_banner():
    """
    The illustrated sample banner image shipped with ClimWeb, imported into the image library once and reused
    """
    Image = get_image_model()
    image = Image.objects.filter(title=SAMPLE_BANNER_TITLE).first()
    if image:
        return image
    
    with open(SAMPLE_BANNER_PATH, "rb") as f:
        image = Image(title=SAMPLE_BANNER_TITLE, file=ImageFile(f, name="anticipatory_action_sample_banner.jpg"))
        image.save()
    return image


def get_template_content():
    """
    Example content for a slow-onset drought situation, for editors to replace
    """
    return {
        "banner_image": get_or_create_sample_banner(),
        "banner_title": _("Know the risk, act before the impact"),
        "hazard": _("Drought"),
        "risk_level": "high",
        "affected_areas": _("Replace with the areas at risk, e.g. North-eastern counties"),
        "situation_last_updated": timezone.localdate(),
        "show_phase": True,
        "phases": [
            ("phase", {"label": _("Normal"), "description": "", "is_current": False}),
            ("phase", {"label": _("Watch"), "is_current": True,
                       "description": _("Forecasts show a raised risk. Partners are monitoring and reviewing plans")}),
            ("phase", {"label": _("Readiness"), "is_current": False,
                       "description": _("Trigger thresholds are close. Partners are preparing to act")}),
            ("phase", {"label": _("Activation"), "is_current": False,
                       "description": _("Trigger reached. Anticipatory actions are under way")}),
        ],
        "risk_summary": "<p>{}</p><p>{}</p>".format(
            _("Below-average rainfall is forecast for the coming season. Pasture and water availability are "
              "expected to decline, with the greatest impact on pastoralist and agro-pastoral livelihoods."),
            _("Replace this summary with what is happening, which areas, sectors and livelihoods may be affected, "
              "how the situation is expected to evolve and why early action is needed."),
        ),
        "key_facts": [
            ("key_fact", {"value": "40%", "label": _("below-normal rainfall expected")}),
            ("key_fact", {"value": "6", "label": _("areas at high risk")}),
            ("key_fact", {"value": _("3 months"), "label": _("expected duration")}),
        ],
        "recommended_actions": [
            ("recommended_action", {
                "audience": _("Farmers"),
                "icon": "",
                "actions": RichText("<ul><li>{}</li><li>{}</li></ul>".format(
                    _("Plant drought-tolerant and early-maturing varieties"),
                    _("Harvest and store water"),
                )),
            }),
            ("recommended_action", {
                "audience": _("Pastoralists"),
                "icon": "",
                "actions": RichText("<ul><li>{}</li><li>{}</li></ul>".format(
                    _("Plan early destocking"),
                    _("Identify dry-season grazing areas and water points"),
                )),
            }),
        ],
        "institutions": [
            ("institution", {
                "name": _("National Disaster Management Authority"),
                "description": _("Coordinates preparedness and response"),
                "page": None,
                "external_url": "https://example.org",
                "logo": None,
            }),
            ("institution", {
                "name": _("Ministry of Agriculture"),
                "description": _("Agricultural extension services"),
                "page": None,
                "external_url": "https://example.org",
                "logo": None,
            }),
        ],
    }


def create_draft_page(parent, user=None, site=None):
    """
    Create an unpublished Anticipatory Action page from the template under the given (home) page.

    Returns (page, created). If a page already exists it is returned unchanged.
    The page is linked as the site's Anticipatory Action page in Important Pages
    only if no page is linked yet, so an existing page keeps working until editors switch.
    """
    existing = get_existing_page()
    if existing:
        return existing, False

    page = AnticipatoryActionPage(
        title=_("Anticipatory Action"),
        slug=get_available_slug(parent),
        live=False,
        **get_template_content(),
    )
    parent.add_child(instance=page)
    page.save_revision(user=user, log_action=True)

    site = site or parent.get_site()
    if site:
        important_pages = ImportantPages.for_site(site)
        if not important_pages.anticipatory_action_page_id:
            important_pages.anticipatory_action_page = page
            important_pages.save()

    return page, True
