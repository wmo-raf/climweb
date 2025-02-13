from django.test import Client, TestCase
from django.urls import reverse


class TestSearchPage(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_search_page(self):
        url = reverse('search')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/search.html')
