from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from forecastmanager.models import City
from wagtail.admin import messages
from wagtail.admin.auth import user_passes_test, user_has_any_page_permission
from wagtail.api.v2.utils import get_full_url
from wagtail_modeladmin.helpers import AdminURLHelper

from .forms import ClimateDataForm
from .models import CityClimateDataPage, DataValue


@user_passes_test(user_has_any_page_permission)
def pre_load_climate_data(request, page_id):
    template = "cityclimate/cities_climate_data_checklist.html"
    context = {}

    page = CityClimateDataPage.objects.filter(pk=page_id)
    if page.exists():
        page = page.first().specific

    context.update({"page": page})

    cities_list = []
    cities = City.objects.all()
    cities_with_data_count = 0

    for city in cities:
        load_data_url = reverse("cityclimate_load_data", args=[page.pk])
        load_data_url = load_data_url + f"?city_id={city.pk}"

        city_info = {
            "city": city,
            "has_data": False,
            "load_data_url": get_full_url(request, load_data_url)
        }

        test_value = DataValue.objects.filter(city=city, parameter__page_id=page.pk).first()
        if test_value:
            city_info.update({"has_data": True})
            cities_with_data_count += 1

        cities_list.append(city_info)

    context.update({"cities_list": cities_list, "cities_with_data_count": cities_with_data_count})

    if not cities_list:
        city_admin_helper = AdminURLHelper(City)
        url = city_admin_helper.get_action_url("index")
        context.update({"cities_list_url": url})

    return render(request, template_name=template, context=context)


@user_passes_test(user_has_any_page_permission)
def load_climate_data(request, page_id):
    template = "cityclimate/load_climate_data.html"
    context = {}

    city_id = request.GET.get("city_id")
    selected_city = None

    if city_id:
        selected_city = City.objects.get(pk=city_id)

    context.update({
        "city": selected_city
    })

    page = CityClimateDataPage.objects.filter(pk=page_id)

    if page.exists():
        page = page.first().specific

    parameters = page.data_parameters.all()
    context.update({"parameters": parameters})

    if request.POST:
        form = ClimateDataForm(request.POST, request.FILES)

        if form.is_valid():
            city = form.cleaned_data.get("city")
            data = form.cleaned_data.get("data")
            date_format = form.cleaned_data.get("date_format")

            records_to_update = []
            records_to_create = []

            for value in data:
                date = value.get("date")
                for parameter in parameters:
                    if value.get(parameter.slug):
                        val = value.get(parameter.slug)
                        unique_data = {"date": date, "city": city, "parameter": parameter}
                        existing_record = DataValue.objects.filter(**unique_data)

                        if existing_record.exists():
                            existing_record = existing_record.first()
                            records_to_update.append({**unique_data, "value": val, "pk": existing_record.pk})
                        else:
                            records_to_create.append({**unique_data, "value": val})

            # bulk create or update. Saves database round trips
            try:
                # update
                if records_to_update:
                    DataValue.objects.bulk_update(
                        [
                            DataValue(**values) for values in records_to_update
                        ],
                        ["value"],
                        batch_size=1000
                    )
                # create
                if records_to_create:
                    DataValue.objects.bulk_create(
                        [DataValue(**values) for values in records_to_create], batch_size=1000
                    )

            except Exception as e:
                print(e)

            messages.success(request, "Data loaded successfully")
            return redirect(reverse("cityclimate_data_checklist", args=(page.pk,)))
        else:
            context.update({"form": form})
            return render(request, template_name=template, context=context)
    else:
        initial_data = {}
        form_kwargs = {}
        if selected_city:
            initial_data.update({"city": selected_city})
            form_kwargs.update({"city": selected_city})

        form_kwargs.update({
            "initial": initial_data
        })

        form = ClimateDataForm(**form_kwargs)
        context["form"] = form

    return render(request, template_name=template, context=context)


def climate_data(request, page_id):
    city_id = request.GET.get("city_id")

    page = CityClimateDataPage.objects.filter(pk=page_id)

    if page.exists():
        page = page.first().specific

    parameters = page.data_parameters.all()
    if city_id:
        param_values = DataValue.objects.filter(city_id=city_id, parameter__in=parameters)
    else:
        param_values = DataValue.objects.filter(parameter__in=parameters)

    values_dict = {}

    for value in param_values:
        date_str = value.date.isoformat()
        if not values_dict.get(date_str):
            values_dict[date_str] = {}
        values_dict[date_str].update({value.parameter.slug: value.value, "city": value.city.name,
                                      "coordinates": [float(coordinate) for coordinate in value.city.coordinates if
                                                      coordinate]})

    values = [{"date": key, **values_dict[key]} for key in values_dict.keys()]

    return JsonResponse(values, safe=False)
