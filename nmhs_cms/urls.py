import os 
from django.conf import settings
from django.urls import include, path, register_converter
from django.contrib import admin

from wagtail.views import serve as wagtail_serve
from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from forecast_manager import urls as forecast_urls
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth.views import LoginView
from home.views import list_forecasts

from search import views as search_views
from capeditor import urls as cap_urls
import environ
import debug_toolbar


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)

if os.path.exists(os.path.join(BASE_DIR, '.env')):
    # reading .env file
    environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


handler500 = 'core.views.handler500'

class IdentifierConverter:
    regex = r'[A-Za-z0-9_-]+'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value

register_converter(IdentifierConverter, 'identifier')

urlpatterns = [
    # path('cms/<slug:slug>/', wagtail_serve, name='wagtailcore_serve'),
    path(f"{os.getenv('BASE_PATH', '')}"+"django-admin/", admin.site.urls),
    path(f"{os.getenv('BASE_PATH', '')}"+"admin/", include(wagtailadmin_urls), name='admin'),
    path(f"{os.getenv('BASE_PATH', '')}"+"documents/", include(wagtaildocs_urls)),
    path(f"{os.getenv('BASE_PATH', '')}"+"forecast/", include(forecast_urls)),
    path(f"{os.getenv('BASE_PATH', '')}"+"list_forecast/", list_forecasts, name="list_forecasts"),
    path(f"{os.getenv('BASE_PATH', '')}"+"cap/", include(cap_urls)),
    path(f"{os.getenv('BASE_PATH', '')}"+"search/", search_views.search, name="search"),

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
                    path(f"{os.getenv('BASE_PATH', '')}"+'__debug__/', include(debug_toolbar.urls)),
                    path(f"{os.getenv('BASE_PATH', '')}"+"test404/", TemplateView.as_view(template_name="404.html")),
                    path(f"{os.getenv('BASE_PATH', '')}"+"test500/", TemplateView.as_view(template_name="500.html")),
                  ] + urlpatterns
    
  

urlpatterns = urlpatterns + i18n_patterns(
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path(f"{os.getenv('BASE_PATH', '')}", include(wagtail_urls)),
    prefix_default_language=False,
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
)
