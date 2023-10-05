from datetime import datetime, timedelta
from itertools import groupby

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from forecastmanager.models import City, Forecast
from forecastmanager.models import DailyWeather


def list_forecasts(request):
    start_date_param = datetime.today()
    end_date_param = start_date_param + timedelta(days=6)
    forecast_data = Forecast.objects.filter(forecast_date__gte=start_date_param.date(),
                                            forecast_date__lte=end_date_param.date(), effective_period__whole_day=True) \
        .order_by('forecast_date') \
        .values('id', 'city__name', 'forecast_date', 'data_value', 'condition', 'effective_period',
                'effective_period__whole_day', 'effective_period__forecast_effective_time')

    # sort the data by city
    data_sorted = sorted(forecast_data, key=lambda x: x['forecast_date'])
    # group the data by city
    grouped_forecast = {}
    for dates, group in groupby(data_sorted, lambda x: x['forecast_date']):
        dates_data = {'dates': dates, 'forecast_items': list(group)}

        # for item in  sorted(city_data['forecast_items'], key=lambda x: x['forecast_date']):
        # date_obj = datetime.strptime( item['forecast_date'], '%Y-%m-%d').date()
        # item['forecast_date'] =item['forecast_date']

        grouped_forecast[dates_data['dates']] = dates_data['forecast_items']

    cities = list(set([d['city__name'] for d in data_sorted]))
    dates = list(set([d['forecast_date'] for d in data_sorted]))

    return render(request, "forecasts_index.html", {
        "forecasts": grouped_forecast,
        "cities": cities,
        "dates": sorted(dates)
    })


def daily_weather(request):
    report = DailyWeather.objects.all().order_by('issued_on').first()

    return render(request, "dailyweather_include.html", {
        "report": report
    })


def city_analysis(request, city_id):
    reordered_cities = None
    cities = City.objects.all()
    curr_city = cities.get(pk=city_id)
    city_names = cities.values('name')

    if len(city_names) > 0:
        # Get all items except the target item
        other_cities = City.objects.exclude(pk=city_id)
        selected_city = City.objects.get(pk=city_id)
        # Combine the target item with the other items
        reordered_cities = [selected_city] + list(other_cities)

    context = {
        'city_name': curr_city.name,
        'city_id': city_id,
        'city_item': reordered_cities,
        'url': HttpResponseRedirect(reverse('city_analysis', kwargs={'city_id': city_id}))
    }

    return render(request, "city_analysis.html", context)
