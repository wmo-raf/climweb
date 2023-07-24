from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path
from forecastmanager import urls as forecastmanager_urls
from wagtail import views as wagtail_views
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.urls import WAGTAIL_FRONTEND_LOGIN_TEMPLATE, serve_pattern
from wagtailcache.cache import cache_page

from pages.cap.views import AlertList, AlertDetail
from pages.home.views import list_forecasts, daily_weather
from pages.search import views as search_views

handler500 = 'base.views.handler500'

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls), name='admin'),
    path("documents/", include(wagtaildocs_urls)),
    path("list_forecast/", list_forecasts, name="list_forecasts"),
    path("daily_weather/", daily_weather, name="daily_weather"),
    path('api/cap/feed.xml', AlertList.as_view(), name="cap_alert_feed"),
    path("api/cap/<uuid:identifier>.xml", AlertDetail.as_view(), name="cap_alert_detail"),
    path("api/satellite-imagery/", include("pages.satellite_imagery.urls")),
    path("api/cityclimate/", include("pages.cityclimate.urls")),

    path("search/", search_views.search, name="search"),

    path("", include("geomanager.urls"), name="geomanager"),
    # path("", include("django_nextjs.urls")),
    path("", include("wagtailsurveyjs.urls")),
    re_path("", include(forecastmanager_urls), name="forecast_api"),
    path("sitemap.xml", sitemap),
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

urlpatterns = urlpatterns + [
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:

    # Copied from wagtail.urls for compatibility with wagtail-cache. See wagtail-cache documentation
    path(
        "_util/authenticate_with_password/<int:page_view_restriction_id>/<int:page_id>/",
        wagtail_views.authenticate_with_password,
        name="wagtailcore_authenticate_with_password",
    ),
    path(
        "_util/login/",
        auth_views.LoginView.as_view(template_name=WAGTAIL_FRONTEND_LOGIN_TEMPLATE),
        name="wagtailcore_login",
    ),
    # Front-end page views are handled through Wagtail's core.views.serve
    # mechanism
    # Custom wagtail pages serving with cache implements from wagtail-cache page
    re_path(serve_pattern, cache_page(wagtail_views.serve), name="wagtail_serve"),
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
]
