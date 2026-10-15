import uuid
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from wagtail.models import Site

from .factories import ServiceIndexPageFactory, ServicePageFactory
from ..models import ServicePage


class TestServicePageMap(TestCase):
    @classmethod
    def setUpTestData(cls):
        # hung off the site root rather than a HomePage, to keep the test about the map section only
        root = Site.objects.get(is_default_site=True).root_page
        index_page = ServiceIndexPageFactory(parent=root)
        cls.page = ServicePageFactory(parent=index_page, map_title="Rainfall outlook")

    def set_layers(self, *layers):
        self.page.map_layers = [
            {"type": "wms_layer", "value": {"layer": layer_id, "enabled": enabled, "icon": "layer-group"}}
            for layer_id, enabled in layers
        ]
        self.page.save()
        return ServicePage.objects.get(pk=self.page.pk)

    def test_no_layers_means_no_map(self):
        self.assertFalse(self.page.has_map)

    def test_deleted_layer_does_not_count(self):
        page = self.set_layers((str(uuid.uuid4()), True))

        self.assertFalse(page.has_map)

    def test_page_without_map_skips_map_section_and_assets(self):
        response = self.client.get(self.page.url)

        self.assertNotContains(response, 'id="home-map"')
        self.assertNotContains(response, "maplibre-gl.js")

    def test_page_with_map_renders_map_section(self):
        with mock.patch.object(ServicePage, "has_map", new_callable=mock.PropertyMock, return_value=True):
            response = self.client.get(self.page.url)

        self.assertContains(response, 'id="home-map"')
        self.assertContains(response, reverse("service-map-settings", args=[self.page.pk]))
        self.assertContains(response, "Rainfall outlook")
        self.assertContains(response, "maplibre-gl.js")

    def test_map_settings_leave_out_deleted_layers_and_city_forecasts(self):
        self.set_layers((str(uuid.uuid4()), True))

        response = self.client.get(reverse("service-map-settings", args=[self.page.pk]))

        self.assertEqual(response.status_code, 200)
        config = response.json()
        self.assertEqual(config["dynamicMapLayers"], [])
        self.assertFalse(config["showLocationForecastLayer"])

    def test_map_settings_404_for_unpublished_page(self):
        self.page.unpublish()

        response = self.client.get(reverse("service-map-settings", args=[self.page.pk]))

        self.assertEqual(response.status_code, 404)
