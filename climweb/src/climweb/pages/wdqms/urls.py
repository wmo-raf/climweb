from django.urls import path

from .views import wdqms_reports

urlpatterns = [
    path("wdqms-reports/", wdqms_reports, name="wdqms-reports"),
]
