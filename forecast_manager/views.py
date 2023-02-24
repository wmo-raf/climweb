from django.shortcuts import render
from .models import City
import json
from django.core import serializers


# Create your views here.
def upload_forecast(request):
    city_ls = list(City.objects.values('name'))
    # data = serializers.serialize('json', city_ls)
    # print(data)

    return render(request, "forecast/upload_forecast.html", {
        "city_ls": json.dumps(city_ls)
    })