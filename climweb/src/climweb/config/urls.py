from climweb_wdqms import urls as climweb_wdqms_urls
from django.conf import settings
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

from climweb.base.registries import plugin_registry
from climweb.base.views import humans, public_health_check
from climweb.pages.search import views as search_views
from .api import api_router

handler500 = 'climweb.base.views.handler500'

ADMIN_URL_PATH = getattr(settings, "ADMIN_URL_PATH", None)
DJANGO_ADMIN_URL_PATH = getattr(settings, "DJANGO_ADMIN_URL_PATH", None)

CLIMWEB_ADDITIONAL_APPS = getattr(settings, "CLIMWEB_ADDITIONAL_APPS", [])

urlpatterns = [
    path("documents/", include(wagtaildocs_urls)),
    
    path("", include("climweb.pages.home.urls")),
    path("", include("climweb.pages.wdqms.urls")),
    path("", include("capcomposer.cap.urls")),
    path("", include("climweb.pages.stations.urls"), name="stations"),
    path("", include("climweb.pages.videos.urls")),
    path("weather/", include("climweb.pages.weather.urls")),
    
    path("", include("geomanager.urls"), name="geomanager"),
    # path("", include("django_nextjs.urls")),
    path("", include("wagtailsurveyjs.urls")),
    path("", include(forecastmanager_urls), name="forecast_api"),
    path("", include(climweb_wdqms_urls), name="climweb_wdqms_api"),
    
    path("sitemap.xml", sitemap),
    path("humans.txt", humans),
    
    path("search/", search_views.search, name="search"),
    path('auth/', include('allauth.urls')),
    
    path('api/v2/', api_router.urls, name="wagtailapi"),
    
    path("api/satellite-imagery/", include("climweb.pages.satellite_imagery.urls")),
    path("api/cityclimate/", include("climweb.pages.cityclimate.urls")),
    path("api/_health/", public_health_check),
]

if "climweb.pages.aviation" in CLIMWEB_ADDITIONAL_APPS:
    urlpatterns += path("", include("climweb.pages.aviation.urls")),

if ADMIN_URL_PATH:
    ADMIN_URL_PATH = ADMIN_URL_PATH.strip("/")
    urlpatterns += path(f"{ADMIN_URL_PATH}/", include(wagtailadmin_urls), name='admin'),

if DJANGO_ADMIN_URL_PATH:
    DJANGO_ADMIN_URL_PATH = DJANGO_ADMIN_URL_PATH.strip("/")
    urlpatterns += path(f"{DJANGO_ADMIN_URL_PATH}/", admin.site.urls, name='django-admin'),

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

# Add the urls of the registered plugins
urlpatterns += plugin_registry.urls

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
