from django.urls import path

from .views import PublicShortenLinkView, redirect_short_link

urlpatterns = [
    path("shorten/", PublicShortenLinkView.as_view(), name="public_shorten_link"),
    path("s/<str:short_code>/", redirect_short_link, name="shortlink_redirect"),
]
