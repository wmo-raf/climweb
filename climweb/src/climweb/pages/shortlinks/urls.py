from django.urls import path

from .views import create_short_link, redirect_short_link

urlpatterns = [
    path("api/shorten/", create_short_link, name="create_short_link"),
    path("s/<str:short_code>/", redirect_short_link, name="shortlink_redirect"),
]
