from adminboundarymanager.models import AdminBoundary
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.test import RequestFactory
from django.utils import timezone
from wagtail.models import Site
from wagtail.test.utils import WagtailPageTestCase

from ..models import SubNationalProductPage, SubNationalRegion
from .factories import (
    ProductIndexPageFactory,
    ProductItemPageFactory,
    SubNationalProductsLandingPageFactory,
    SubNationalProductPageFactory,
    SubNationalRegionFactory,
)


def create_boundary(level, gid_1, name_1, gid_2=None, name_2=None, offset=0):
    polygon = Polygon(((offset, 0), (offset, 1), (offset + 1, 1), (offset + 1, 0), (offset, 0)))
    return AdminBoundary.objects.create(
        level=level, gid_0="KE", name_0="Kenya",
        gid_1=gid_1, name_1=name_1, gid_2=gid_2, name_2=name_2,
        geom=MultiPolygon(polygon),
    )


class TestSubNationalProducts(WagtailPageTestCase):
    @classmethod
    def setUpTestData(cls):
        create_boundary(1, "KE01", "Nairobi")
        create_boundary(1, "KE02", "Mombasa", offset=2)
        create_boundary(2, "KE01", "Nairobi", "KE0101", "Westlands")
        create_boundary(2, "KE02", "Mombasa", "KE0201", "Nyali", offset=2)
        
        root_page = Site.objects.get(is_default_site=True).root_page
        index_page = ProductIndexPageFactory(parent=root_page)
        cls.landing_page = SubNationalProductsLandingPageFactory(parent=index_page)
        
        cls.coast = SubNationalRegionFactory(name="Coast")
        cls.nairobi = SubNationalRegionFactory(name="Nairobi", admin_level=1, admin_gid="KE01")
        cls.westlands = SubNationalRegionFactory(name="Westlands", admin_level=2, admin_gid="KE0101")
        # named differently from the boundary data
        cls.nyali = SubNationalRegionFactory(name="Nyali Beach", admin_level=2, admin_gid="KE0201")
        
        cls.nairobi_page = SubNationalProductPageFactory(parent=cls.landing_page, region=cls.nairobi)
        cls.westlands_page = SubNationalProductPageFactory(parent=cls.landing_page, region=cls.westlands)
        cls.nyali_page = SubNationalProductPageFactory(parent=cls.landing_page, region=cls.nyali)
        cls.unlinked_page = SubNationalProductPageFactory(parent=cls.landing_page, region=cls.coast)
    
    def filtered_ids(self, **params):
        request = RequestFactory().get("/", params)
        return set(self.landing_page.filter_items(request).values_list("id", flat=True))
    
    def test_filters_group_sub_districts_under_districts(self):
        filters = self.landing_page.filters
        districts = [
            (d["gid"], d["name"], d["count"], [(s["gid"], s["name"], s["count"]) for s in d["sub_districts"]])
            for d in filters["districts"]
        ]
        
        self.assertEqual(districts, [
            ("KE02", "Mombasa", 1, [("KE0201", "Nyali Beach", 1)]),
            ("KE01", "Nairobi", 2, [("KE0101", "Westlands", 1)]),
        ])
        self.assertEqual(filters["other_regions"], [{"id": self.coast.id, "name": "Coast", "count": 1}])
    
    def test_filter_by_district_includes_its_sub_districts(self):
        self.assertEqual(self.filtered_ids(district="KE01"), {self.nairobi_page.id, self.westlands_page.id})
    
    def test_sub_district_narrows_its_district(self):
        self.assertEqual(self.filtered_ids(district="KE02", subdistrict="KE0201"), {self.nyali_page.id})
        self.assertEqual(self.filtered_ids(district="KE01", subdistrict="KE0101"), {self.westlands_page.id})
    
    def test_region_is_combined_with_boundary_filters(self):
        self.assertEqual(
            self.filtered_ids(district="KE01", region=str(self.coast.id)),
            {self.nairobi_page.id, self.westlands_page.id, self.unlinked_page.id},
        )
    
    def test_no_filter_returns_all(self):
        self.assertEqual(len(self.filtered_ids()), 4)
    
    def test_map_config(self):
        request = RequestFactory().get("/", {"district": "KE02"})
        request.site = self.landing_page.get_site()
        config = self.landing_page.get_map_config(request)
        
        self.assertEqual(config["selectedDistricts"], ["KE02"])
        # zoomed to the selected district
        self.assertEqual(config["bounds"], [2.0, 0.0, 3.0, 1.0])
        self.assertEqual(set(config["subDistricts"]), {"KE0101", "KE0201"})
        self.assertEqual(len(config["labels"]["features"]), 4)
        
        request = RequestFactory().get("/")
        request.site = self.landing_page.get_site()
        # zoomed to all areas with products
        self.assertEqual(self.landing_page.get_map_config(request)["bounds"], [0.0, 0.0, 3.0, 1.0])
    
    def test_active_filters(self):
        request = RequestFactory().get("/", {"district": "KE01", "subdistrict": "KE0101"})
        chips = self.landing_page.get_active_filters(request)
        
        self.assertEqual(chips, [
            {"label": "Nairobi", "url": "?"},
            {"label": "Westlands", "url": "?district=KE01"},
        ])
    
    def test_listing_details(self):
        self.westlands_page.introduction_image = None
        self.landing_page.add_listing_details([self.westlands_page])
        
        self.assertEqual(self.westlands_page.location["district"]["name"], "Nairobi")
        self.assertEqual(self.westlands_page.location["sub_district"]["name"], "Westlands")
        self.assertIsNone(self.westlands_page.latest_update)
        self.assertTrue(self.westlands_page.boundary_thumbnail["path"].startswith("M"))
    
    def test_pages_render(self):
        self.assertPageIsRenderable(self.landing_page)
        self.assertPageIsRenderable(self.landing_page, query_data={"district": "KE01"})
        self.assertPageIsRenderable(self.westlands_page)
    
    def region_form(self, data=None, instance=None):
        form_class = SubNationalRegion.snippet_viewset.get_edit_handler().get_form_class()
        return form_class(data, instance=instance or SubNationalRegion(), for_user=None)
    
    def test_region_form_sets_admin_level_and_code(self):
        form = self.region_form(instance=self.westlands)
        self.assertEqual(form.initial["admin_boundary"], "2:KE0101")
        
        form = self.region_form({"name": "Nyali", "admin_boundary": "2:KE0201"})
        self.assertTrue(form.is_valid(), form.errors)
        region = form.save()
        self.assertEqual((region.admin_level, region.admin_gid), (2, "KE0201"))
        self.assertEqual(region.boundary.name_2, "Nyali")
        
        form = self.region_form({"name": "Nyali", "admin_boundary": ""}, instance=region)
        self.assertTrue(form.is_valid(), form.errors)
        region = form.save()
        self.assertIsNone(region.admin_level)
        self.assertIsNone(region.admin_gid)
    
    def test_region_form_uses_level_names(self):
        self.landing_page.admin_level_1_name = "Region"
        self.landing_page.admin_level_2_name = "District"
        self.landing_page.save()
        
        groups = [label for label, _choices in self.region_form().fields["admin_boundary"].choices[1:]]
        self.assertEqual(groups, ["Region (admin level 1)", "District (admin level 2)"])
    
    def test_product_page_context(self):
        request = RequestFactory().get("/")
        request.site = self.landing_page.get_site()
        context = self.nyali_page.get_context(request)
        
        self.assertEqual(context["location"]["district"]["name"], "Mombasa")
        self.assertEqual(context["location"]["sub_district"]["name"], "Nyali Beach")
        self.assertEqual(context["area_name"], "Sub-district")
        self.assertTrue(context["boundary_thumbnail"]["path"].startswith("M"))
        self.assertFalse(context["has_updates"])
        # each page has its own product, so there are no other areas to switch to
        self.assertIsNone(context["other_areas"])
    
    def test_product_page_switches_between_areas_of_the_same_product(self):
        SubNationalProductPage.objects.filter(pk=self.westlands_page.pk).update(product=self.nyali_page.product)
        
        request = RequestFactory().get("/")
        request.site = self.landing_page.get_site()
        context = self.nyali_page.get_context(request)
        
        self.assertEqual([p.pk for p in context["other_areas"]], [self.nyali_page.pk, self.westlands_page.pk])
    
    def test_product_page_renders_with_updates(self):
        item_types = self.nairobi_page.product.product_item_types
        ProductItemPageFactory(
            parent=self.nairobi_page,
            products__0__image_product__product_type=item_types[0][0],
            products__0__image_product__date=timezone.now().date(),
        )
        
        response = self.client.get(self.nairobi_page.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["has_updates"])
        self.assertContains(response, "pub-filter")
        self.assertNotContains(response, "subnational-detail-empty")
    
    def test_landing_page_shows_level_names(self):
        self.landing_page.admin_level_1_name = "Region"
        self.landing_page.save()
        
        response = self.client.get(self.landing_page.url)
        self.assertContains(response, '<label for="subnational-district" class="subnational-filter-label">Region</label>',
                            html=True)
