from capeditor import urls as cap_urls
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from forecast_manager import urls as forecast_urls
from pages.home.views import list_forecasts
from pages.search import views as search_views

handler500 = 'base.views.handler500'

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls), name='admin'),
    path("documents/", include(wagtaildocs_urls)),
    path("forecast/", include(forecast_urls)),
    path("list_forecast/", list_forecasts, name="list_forecasts"),
    path("cap/", include(cap_urls)),
    path("search/", search_views.search, name="search"),

    path("", include("geomanager.urls")),
    path("", include("django_nextjs.urls")),
    path("", include("wagtailsurveyjs.urls")),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.views.generic import TemplateView

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),
                      path("test404/", TemplateView.as_view(template_name="404.html")),
                      path("test500/", TemplateView.as_view(template_name="500.html")),
                  ] + urlpatterns

urlpatterns = urlpatterns + i18n_patterns(
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path(f"", include(wagtail_urls)),
    prefix_default_language=False,
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
)
