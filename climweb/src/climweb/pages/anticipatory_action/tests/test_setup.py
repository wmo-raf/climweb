from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from wagtail.models import Site

from climweb.base.models import ImportantPages
from climweb.pages.flex_page.models import FlexPage
from climweb.pages.home.tests.factories import get_or_create_homepage
from ..models import AnticipatoryActionPage
from ..setup import create_draft_page


class TestCreateDraftPage(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.home_page = get_or_create_homepage()
        cls.site = Site.objects.get(is_default_site=True)
    
    def test_creates_unpublished_page_from_template_and_links_it(self):
        page, created = create_draft_page(self.home_page)
        
        self.assertTrue(created)
        self.assertFalse(page.live)
        self.assertEqual(page.get_parent().pk, self.home_page.pk)
        self.assertEqual(page.slug, "anticipatory-action")
        self.assertEqual(page.hazard, "Drought")
        self.assertEqual(len(page.key_facts), 3)
        self.assertEqual(page.action_audiences, ["Farmers", "Pastoralists"])
        self.assertEqual(len(page.institutions), 2)
        self.assertIsNotNone(page.banner_image)
        self.assertTrue(page.show_phase)
        self.assertEqual(page.current_phase["label"], "Watch")
        self.assertEqual(ImportantPages.for_site(self.site).anticipatory_action_page_id, page.pk)
    
    def test_template_draft_renders(self):
        page, _ = create_draft_page(self.home_page)
        page.save_revision().publish()
        resp = self.client.get(page.get_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Plan early destocking")
    
    def test_sample_banner_is_imported_once(self):
        from ..setup import get_or_create_sample_banner
        first = get_or_create_sample_banner()
        second = get_or_create_sample_banner()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual((first.width, first.height), (2400, 900))
    
    def test_returns_existing_page(self):
        first, _ = create_draft_page(self.home_page)
        second, created = create_draft_page(self.home_page)
        
        self.assertFalse(created)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(AnticipatoryActionPage.objects.count(), 1)
    
    def test_existing_flex_page_keeps_slug_and_link(self):
        flex_page = FlexPage(title="Anticipatory Action", slug="anticipatory-action", banner_title="Anticipatory Action")
        self.home_page.add_child(instance=flex_page)
        important_pages = ImportantPages.for_site(self.site)
        important_pages.anticipatory_action_page = flex_page
        important_pages.save()
        
        page, _ = create_draft_page(self.home_page)
        
        self.assertEqual(page.slug, "anticipatory-action-2")
        self.assertEqual(ImportantPages.for_site(self.site).anticipatory_action_page_id, flex_page.pk)
    
    def test_management_command(self):
        out = StringIO()
        call_command("create_anticipatory_action_page", stdout=out)
        self.assertIn("Created draft", out.getvalue())
        
        out = StringIO()
        call_command("create_anticipatory_action_page", stdout=out)
        self.assertIn("already exists", out.getvalue())


class TestAddPageChoice(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.home_page = get_or_create_homepage()
        cls.user = get_user_model().objects.create_superuser("admin", "admin@example.com", "password")
    
    def setUp(self):
        self.client.force_login(self.user)
        self.add_url = reverse("wagtailadmin_pages:add",
                               args=["anticipatory_action", "anticipatoryactionpage", self.home_page.pk])
        self.template_url = reverse("anticipatory_action_create_from_template", args=[self.home_page.pk])
    
    def test_adding_page_offers_template_or_scratch(self):
        resp = self.client.get(self.add_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Use template")
        self.assertContains(resp, "Start blank")
        self.assertContains(resp, self.template_url)
    
    def test_from_scratch_shows_blank_form(self):
        resp = self.client.get(self.add_url + "?from_scratch=1")
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "Use template")
        self.assertContains(resp, 'name="banner_title"')
    
    def test_use_template_creates_draft_and_opens_editor(self):
        resp = self.client.post(self.template_url)
        page = AnticipatoryActionPage.objects.get()
        self.assertFalse(page.live)
        self.assertRedirects(resp, reverse("wagtailadmin_pages:edit", args=[page.pk]), fetch_redirect_response=False)
    
    def test_template_is_post_only(self):
        self.assertEqual(self.client.get(self.template_url).status_code, 405)
        self.assertFalse(AnticipatoryActionPage.objects.exists())
    
    def test_template_requires_permission(self):
        editor = get_user_model().objects.create_user("editor", "editor@example.com", "password")
        editor.user_permissions.add(Permission.objects.get(codename="access_admin"))
        self.client.force_login(editor)
        
        # Wagtail admin turns PermissionDenied into a redirect to the dashboard with an error message
        resp = self.client.post(self.template_url)
        self.assertRedirects(resp, reverse("wagtailadmin_home"), fetch_redirect_response=False)
        self.assertFalse(AnticipatoryActionPage.objects.exists())
