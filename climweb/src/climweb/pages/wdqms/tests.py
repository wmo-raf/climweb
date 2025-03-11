from django.test import Client, TestCase
from django.urls import reverse


class TestWDQMSReportPage(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_wdqms_reports_page(self):
        url = reverse('wdqms-reports')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wdqms/report_index.html')
