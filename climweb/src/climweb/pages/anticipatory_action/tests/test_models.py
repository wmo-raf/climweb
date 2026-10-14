import json
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from shapely.geometry import box
from wagtail.models import Site
from wagtail.rich_text import RichText
from wagtail.test.utils import WagtailPageTestCase

from climweb.base.models import ImportantPages
from climweb.pages.home.tests.factories import get_or_create_homepage
from climweb.pages.news.tests.factories import NewsIndexPageFactory, NewsPageFactory
from ..cap import info_matches
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
    
    def test_status_bar_and_phase_rendered(self):
        self.page.show_phase = True
        self.page.current_phase = "readiness"
        self.page.save_revision().publish()
        
        resp = self.client.get(self.page.get_url())
        self.assertContains(resp, "aa-risk-level--high")
        self.assertContains(resp, "North-eastern counties")
        self.assertContains(resp, 'class="aa-phase-step is-current"')
    
    def test_phase_states(self):
        self.page.current_phase = "readiness"
        states = {phase["value"]: phase["state"] for phase in self.page.phases}
        self.assertEqual(states, {
            "normal": "past", "watch": "past", "readiness": "current", "activation": "upcoming",
        })
    
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
