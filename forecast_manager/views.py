import json
from itertools import groupby

from datetime import datetime, timedelta
from django.shortcuts import render
from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers

from .models import City, Forecast, ConditionCategory


def list_forecasts(request):

    start_date_param = datetime.today()
    end_date_param = start_date_param + timedelta(days=6)
    forecast_data = Forecast.objects.filter(forecast_date__gte=start_date_param.date(),  forecast_date__lte=end_date_param.date())\
            .order_by('forecast_date')\
            .values('id','city__name','forecast_date', 'max_temp', 'min_temp', 'wind_speed', 'wind_direction', 'condition__title','condition__icon_image', 'condition__icon_image__file')
            # .annotate(
            #     forecast_date_str = Cast(
            #         TruncDate('forecast_date', DateField()), CharField(),
            #     ),
            # )

    # sort the data by city
    data_sorted = sorted(forecast_data, key=lambda x: x['city__name'])
    # group the data by city
    grouped_forecast = {}
    for city, group in groupby(data_sorted, lambda x: x['city__name']):
            city_data = {'city':city, 'forecast_items': list(group)}

            for item in  sorted(city_data['forecast_items'], key=lambda x: x['forecast_date']):
                # date_obj = datetime.strptime( item['forecast_date'], '%Y-%m-%d').date()
                item['forecast_date'] =item['forecast_date']

            grouped_forecast[city_data['city']]  = city_data['forecast_items']
            
    cities = list(set([d['city__name'] for d in data_sorted]))
    dates = list(set([d['forecast_date'] for d in data_sorted]))    
    
    print(dates)
    return render(request, "forecasts_index.html", {
        "forecasts":grouped_forecast,
        "cities":cities,
        "dates":sorted(dates)
    })

# Create your views here.
def upload_forecast(request):
    city_ls = City.objects.all()
    weather_condition_ls = ConditionCategory.objects.all()
    # data = serializers.serialize('json', city_ls)
    # print(data)

    return render(request, "admin/forecast.html", {
        "city_ls": serializers.serialize('json', city_ls, fields = ('name', 'id')),
        "weather_condition_ls":serializers.serialize('json',weather_condition_ls, fields = ('title', 'id'))
    })


@csrf_exempt
def save_data(request):
    if request.method == 'POST':
        data = json.loads(request.POST.get('data', None))
        if len(data) > 0:
            # Iterate through the data and create or update Parent and Child objects
            try:

                for row in data:
                    # Get the name of the parent from the first column
                    parent_name = row['city']
                    # Try to get an existing parent with the same name, or create a new one
                    city = City.objects.get(name=parent_name)
                    condtion = ConditionCategory.objects.get(title=row['condition'])
                    # Create or update the child object with the parent and the name from the second column

                    Forecast.objects.update_or_create(
                        forecast_date=row['forecast_date'],
                        city=city, 
                    defaults={
                        'max_temp':row['max_temp'],
                        'min_temp':row['min_temp'],
                        'wind_direction':row['wind_direction'],
                        'wind_speed':row['wind_speed'],
                        'condition':condtion,
                    })
                return JsonResponse({'success': True})

            except IntegrityError as e:
                return JsonResponse({'error': 'Please fill in all required fields'},  status=400,  safe=False)
    else:
        return JsonResponse({'error': 'Invalid request method.'},  status=400,  safe=False)


def get_data(request):
    start_date_param = request.GET.get('start_date', None)
    end_date_param = request.GET.get('end_date', None)
    city_id = request.GET.get('city_id', None)
    forecast_data = Forecast.objects.filter(city_id=city_id, forecast_date__gte=start_date_param,  forecast_date__lte=end_date_param).values('city__name','forecast_date', 'max_temp', 'min_temp', 'wind_speed', 'wind_direction', 'condition__title')

    if city_id is not None:
        return JsonResponse(list(forecast_data), safe=False)

    else:
        return JsonResponse({'error': 'City ID not provided.'})