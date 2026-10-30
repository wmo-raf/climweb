import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from shapely.geometry import box
from wagtail.models import Site
from wagtail.rich_text import RichText
from wagtail.test.utils import WagtailPageTestCase
from wagtail.test.utils.form_data import inline_formset, nested_form_data, streamfield

from climweb.base.models import ImportantPages
from climweb.pages.home.tests.factories import get_or_create_homepage
from climweb.pages.news.tests.factories import NewsIndexPageFactory, NewsPageFactory
from ..cap import info_matches
from ..models import AnticipatoryActionPage
from .factories import AnticipatoryActionPageFactory


class TestAnticipatoryActionPage(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        cls.page = AnticipatoryActionPageFactory(parent=home_page)
        
        news_index = NewsIndexPageFactory(parent=home_page)
        cls.aa_news = NewsPageFactory(parent=news_index, is_anticipatory_action=True)
        cls.other_news = NewsPageFactory(parent=news_index)
    
    def test_page_render(self):
        self.assertPageIsRenderable(self.page)
    
    def test_can_create_under_homepage_only(self):
        from climweb.pages.home.models import HomePage
        from ..models import AnticipatoryActionPage
        self.assertAllowedParentPageTypes(AnticipatoryActionPage, {HomePage})
    
    def test_latest_updates_only_include_flagged_content(self):
        self.assertEqual(self.page.latest_updates, [self.aa_news])
    
    def ready_set_go(self, current):
        return [
            ("phase", {"label": label, "description": f"{label} description", "is_current": label == current})
            for label in ["Ready", "Set", "Go"]
        ]
    
    def test_status_bar_and_phase_rendered(self):
        self.page.show_phase = True
        self.page.phases = self.ready_set_go("Set")
        self.page.save_revision().publish()
        
        resp = self.client.get(self.page.get_url())
        self.assertContains(resp, "aa-risk-level--high")
        self.assertContains(resp, "North-eastern counties")
        self.assertContains(resp, 'class="aa-phase-step is-current"')
        self.assertContains(resp, "Set description")
        self.assertNotContains(resp, "Ready description")
    
    def test_default_phases(self):
        page = AnticipatoryActionPage()
        self.assertEqual([step["label"] for step in page.phase_steps],
                         ["Normal", "Watch", "Readiness", "Activation"])
        self.assertEqual(page.current_phase["label"], "Normal")
    
    def test_phase_states(self):
        self.page.phases = self.ready_set_go("Set")
        states = {step["label"]: step["state"] for step in self.page.phase_steps}
        self.assertEqual(states, {"Ready": "past", "Set": "current", "Go": "upcoming"})
    
    def test_only_one_current_phase_allowed(self):
        from wagtail.blocks.stream_block import StreamBlockValidationError
        block = AnticipatoryActionPage._meta.get_field("phases").stream_block
        value = block.to_python([
            {"type": "phase", "value": {"label": "Ready", "description": "", "is_current": True}},
            {"type": "phase", "value": {"label": "Set", "description": "", "is_current": True}},
        ])
        with self.assertRaises(StreamBlockValidationError):
            block.clean(value)
    
    def test_phases_clean_accepts_ignore_required_constraints(self):
        from wagtail.blocks.stream_block import StreamBlockValidationError
        block = AnticipatoryActionPage._meta.get_field("phases").stream_block
        value = block.to_python([
            {"type": "phase", "value": {"label": "Ready", "description": "", "is_current": True}},
            {"type": "phase", "value": {"label": "Set", "description": "", "is_current": False}},
        ])
        block.clean(value, ignore_required_constraints=True)
        
        value = block.to_python([
            {"type": "phase", "value": {"label": "Ready", "description": "", "is_current": True}},
            {"type": "phase", "value": {"label": "Set", "description": "", "is_current": True}},
        ])
        with self.assertRaises(StreamBlockValidationError):
            block.clean(value, ignore_required_constraints=True)
    
    def test_phases_form_field_clean(self):
        # the admin form field is optional, so Wagtail cleans it with ignore_required_constraints=True
        field = AnticipatoryActionPage._meta.get_field("phases").formfield()
        block = field.block
        value = block.to_python([
            {"type": "phase", "value": {"label": "Ready", "description": "", "is_current": True}},
        ])
        self.assertEqual(len(field.clean(value)), 1)
    
    def test_shown_phase_needs_a_current_phase(self):
        from django.core.exceptions import ValidationError
        self.page.show_phase = True
        self.page.phases = [("phase", {"label": "Ready", "description": "", "is_current": False})]
        with self.assertRaises(ValidationError):
            self.page.clean()
        
        self.page.show_phase = False
        self.page.clean()
    
    def test_phase_hidden_by_default(self):
        resp = self.client.get(self.page.get_url())
        self.assertNotContains(resp, "aa-phase-steps")
    
    def test_action_audiences_are_unique_and_ordered(self):
        self.page.recommended_actions = [
            ("recommended_action", {"audience": "Farmers", "actions": RichText("<p>a</p>")}),
            ("recommended_action", {"audience": "Pastoralists", "actions": RichText("<p>b</p>")}),
            ("recommended_action", {"audience": "Farmers", "actions": RichText("<p>c</p>")}),
        ]
        self.assertEqual(self.page.action_audiences, ["Farmers", "Pastoralists"])
    
    def test_map_settings_endpoint(self):
        url = reverse("anticipatory-action-map-settings", args=[self.page.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        config = resp.json()
        self.assertFalse(config["showLocationForecastLayer"])
        self.assertEqual(config["dynamicMapLayers"], [])
    
    def test_map_settings_endpoint_requires_live_page(self):
        self.page.unpublish()
        try:
            url = reverse("anticipatory-action-map-settings", args=[self.page.pk])
            self.assertEqual(self.client.get(url).status_code, 404)
        finally:
            self.page.save_revision().publish()


class TestAnticipatoryActionPageAdmin(WagtailPageTestCase):
    def setUp(self):
        self.home_page = get_or_create_homepage()
        user = get_user_model().objects.create_superuser("admin", "admin@example.com", "password")
        self.client.force_login(user)
    
    def post_data(self, **extra):
        return nested_form_data({
            "title": "Anticipatory Action",
            "slug": "anticipatory-action",
            "banner_title": "Know the risk, act before the impact",
            "risk_summary_title": "What's happening",
            "map_title": "Where",
            "institutions_heading": "Preparedness and response",
            "show_cap_alerts": "on",
            "phases": streamfield([
                ("phase", {"label": "Ready", "description": "", "is_current": "on"}),
                ("phase", {"label": "Set", "description": ""}),
            ]),
            "key_facts": streamfield([]),
            "recommended_actions": streamfield([]),
            "extra_content": streamfield([]),
            "map_layers": streamfield([]),
            "cap_areas": streamfield([]),
            "institutions": streamfield([]),
            "products": inline_formset([]),
            "applications": inline_formset([]),
            **extra,
        })
    
    def create(self, **extra):
        url = reverse("wagtailadmin_pages:add",
                      args=("anticipatory_action", "anticipatoryactionpage", self.home_page.pk))
        return self.client.post(url, self.post_data(**extra))
    
    def test_create_draft_in_admin(self):
        response = self.create()
        page = AnticipatoryActionPage.objects.get()
        self.assertRedirects(response, reverse("wagtailadmin_pages:edit", args=(page.pk,)))
        self.assertFalse(page.live)
        self.assertEqual(page.current_phase["label"], "Ready")
    
    def test_publish_in_admin(self):
        response = self.create(**{"action-publish": "publish"})
        self.assertRedirects(response, reverse("wagtailadmin_explore", args=(self.home_page.pk,)),
                             fetch_redirect_response=False)
        self.assertTrue(AnticipatoryActionPage.objects.get().live)
    
    def test_admin_rejects_two_current_phases(self):
        data = self.post_data()
        data["phases-1-value-is_current"] = "on"
        url = reverse("wagtailadmin_pages:add",
                      args=("anticipatory_action", "anticipatoryactionpage", self.home_page.pk))
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Only one phase can be the current phase")
        self.assertFalse(AnticipatoryActionPage.objects.exists())


class TestAnticipatoryActionButton(TestCase):
    @classmethod
    def setUpTestData(cls):
        home_page = get_or_create_homepage()
        cls.page = AnticipatoryActionPageFactory(parent=home_page)
        cls.site = Site.objects.get(is_default_site=True)
    
    def get_settings(self, **kwargs):
        important_pages = ImportantPages.for_site(self.site)
        important_pages.anticipatory_action_page = self.page
        for key, value in kwargs.items():
            setattr(important_pages, key, value)
        important_pages.save()
        return important_pages
    
    def test_button_shown_by_default(self):
        self.assertEqual(self.get_settings().anticipatory_action_button_page, self.page)
    
    def test_button_hidden_when_toggled_off(self):
        settings = self.get_settings(show_anticipatory_action_button=False)
        self.assertIsNone(settings.anticipatory_action_button_page)
    
    def test_button_hidden_after_expiry(self):
        settings = self.get_settings(anticipatory_action_button_expires_at=timezone.now() - timedelta(minutes=1))
        self.assertIsNone(settings.anticipatory_action_button_page)
    
    def test_button_shown_before_expiry(self):
        settings = self.get_settings(anticipatory_action_button_expires_at=timezone.now() + timedelta(days=1))
        self.assertEqual(settings.anticipatory_action_button_page, self.page)
    
    def test_button_rendered_in_header(self):
        self.get_settings(anticipatory_action_button_label="Drought Risk")
        resp = self.client.get("/")
        self.assertContains(resp, "util-link--anticipatory")
        self.assertContains(resp, "Drought Risk")
        
        self.get_settings(show_anticipatory_action_button=False)
        resp = self.client.get("/")
        self.assertNotContains(resp, "util-link--anticipatory")


class FakeInfoValue(dict):
    def __init__(self, event, geometries):
        super().__init__(event=event)
        self.features = [{"type": "Feature", "geometry": geometry} for geometry in geometries]


class TestCapInfoMatching(TestCase):
    area = box(30, 5, 32, 7)
    inside = json.loads(json.dumps(box(30.5, 5.5, 31, 6).__geo_interface__))
    outside = json.loads(json.dumps(box(40, 10, 41, 11).__geo_interface__))
    
    def test_no_filters_match_everything(self):
        self.assertTrue(info_matches(FakeInfoValue("Flood", [self.outside]), set(), []))
    
    def test_event_type_filter(self):
        self.assertTrue(info_matches(FakeInfoValue("Drought", []), {"Drought"}, []))
        self.assertFalse(info_matches(FakeInfoValue("Flood", []), {"Drought"}, []))
    
    def test_area_filter(self):
        self.assertTrue(info_matches(FakeInfoValue("Drought", [self.inside]), set(), [self.area]))
        self.assertFalse(info_matches(FakeInfoValue("Drought", [self.outside]), set(), [self.area]))
    
    def test_event_and_area_filters_combined(self):
        self.assertTrue(info_matches(FakeInfoValue("Drought", [self.outside, self.inside]), {"Drought"}, [self.area]))
        self.assertFalse(info_matches(FakeInfoValue("Flood", [self.inside]), {"Drought"}, [self.area]))
    
    def test_invalid_geometry_is_ignored(self):
        info = FakeInfoValue("Drought", [{"type": "Polygon", "coordinates": "bad"}])
        self.assertFalse(info_matches(info, set(), [self.area]))
