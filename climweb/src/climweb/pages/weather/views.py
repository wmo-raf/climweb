from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from forecastmanager.forecast_settings import ForecastSetting
from forecastmanager.models import City, Forecast
from forecastmanager.serializers import ForecastSerializer
from wagtail.api.v2.utils import get_full_url
from wagtailcache.settings import wagtailcache_settings

from climweb.base.cache import wagcache
from climweb.pages.home.models import HomeMapSettings
from climweb.pages.weather.utils import get_city_forecast_detail_data


def get_home_forecast_widget(request):
    forecast_setting = ForecastSetting.for_request(request)
    
    city_slug = request.GET.get('city')
    context = {}
    
    home_settings = HomeMapSettings.for_request(request)
    show_forecast_attribution = home_settings.show_forecast_attribution
    external_source = forecast_setting.enable_auto_forecast
    if external_source and show_forecast_attribution:
        source_name = "Yr.no"
        source_url = "https://www.yr.no"
        context.update({
            "external_source_attribution": _(
                "Forecast Data Source: %(forecast_source)s"
            ) % {"forecast_source": source_name},
            "external_source_url": source_url,
        })
    
    if city_slug:
        city = City.objects.filter(slug=city_slug).first()
        if city is None:
            context.update({
                "error": True,
                "error_message": _("Location not found. Please search for a different location.")
            })
            return JsonResponse(context, status=404)
    else:
        city = forecast_setting.default_city
        if not city:
            city = City.objects.first()
    
    if city is None:
        context.update({
            "error": True,
            "error_message": _("No location set in the system. Please contact the administrator."),
        })
        
        return render(request, 'weather/widgets/location_forecast_single_slider.html', context)
    
    city_detail_page = forecast_setting.weather_detail_page
    
    if city_detail_page:
        # Try getting the city detail page URL. If it fails, ignore it.
        # this is here because a different page than what is expected might be set
        try:
            city_detail_page = city_detail_page.specific
            city_detail_page_url = city_detail_page.get_full_url(request) + city_detail_page.reverse_subpage(
                "daily_table_for_city", kwargs={"city_slug": city.slug})
            context.update({
                "city_detail_page_url": city_detail_page_url,
            })
        except Exception:
            pass
    
    city_search_url = get_full_url(request, reverse("cities-list"))
    context.update({
        "city_search_url": city_search_url,
    })
    
    if forecast_setting.weather_reports_page:
        context.update({
            "weather_reports_page_url": forecast_setting.weather_reports_page.get_full_url(request)
        })
    
    if wagtailcache_settings.WAGTAIL_CACHE:
        response = wagcache.get(f"city_forecast_widget_data_{city.slug}")
    else:
        response = None
    
    if response is None:
        forecast_periods_count = forecast_setting.periods.count()
        
        multi_period = forecast_periods_count > 1
        
        data = get_city_forecast_detail_data(city, multi_period=multi_period, request=request,
                                             for_home_widget=True)
        
        context.update({
            "city": city,
            "show_condition_label": forecast_setting.show_conditions_label_on_widget,
            "use_period_labels": forecast_setting.use_period_labels,
            **data,
        })
        
        if multi_period:
            response = render(request, 'weather/widgets/location_forecast_multiple_slider.html', context)
        else:
            response = render(request, 'weather/widgets/location_forecast_single_slider.html', context)
        
        if wagtailcache_settings.WAGTAIL_CACHE:
            # Cache the response for 20 minutes
            wagcache.set(f"city_forecast_widget_data_{city.slug}", response, 60 * 20)
    
    return response


def get_home_map_forecast(request):
    forecast_setting = ForecastSetting.for_request(request)
    forecast_periods_count = forecast_setting.periods.count()
    
    multi_period = forecast_periods_count > 1
    
    if multi_period:
        forecasts = Forecast.objects.filter(forecast_date=timezone.localtime().date())
    else:
        forecasts = Forecast.objects.filter(forecast_date__gte=timezone.localtime().date())
    
    forecast_data = ForecastSerializer(forecasts, many=True, context={"request": request, }).data
    
    res_data = {
        "data": forecast_data,
        "multi_period": multi_period
    }
    
    return JsonResponse(res_data, safe=False)
