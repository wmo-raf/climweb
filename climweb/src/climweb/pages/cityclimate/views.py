import datetime

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from forecastmanager.models import City
from wagtail.admin import messages
from wagtail.admin.auth import user_passes_test, user_has_any_page_permission
from wagtail.api.v2.utils import get_full_url
from wagtail_modeladmin.helpers import AdminURLHelper

from .constants import DATE_FORMAT_CHOICES_PARSE_PARAMS
from .forms import ClimateDataForm
from .models import CityClimateDataPage, DataValue
from .utils import get_climatology_page_data


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
        load_data_url = reverse("cityclimate_load_data", args=[page.pk, city.id])
        
        city_info = {
            "city": city,
            "has_data": False,
            "load_data_url": get_full_url(request, load_data_url),
            "delete_data_url": reverse("confirm_delete_city_climate_data", args=[page.pk, city.id]),
            "view_data_url": reverse("view_city_climate_data", args=[page.pk, city.id])
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
def load_city_climate_data(request, page_id, city_id):
    page = get_object_or_404(CityClimateDataPage, pk=page_id).specific
    selected_city = get_object_or_404(City, pk=city_id)
    
    template = "cityclimate/load_climate_data.html"
    context = {}
    
    context.update({
        "city": selected_city
    })
    
    parameters = page.data_parameters.all()
    context.update({"parameters": parameters})
    
    if request.POST:
        form = ClimateDataForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                city = form.cleaned_data.get("city")
                data = form.cleaned_data.get("data")
                file_date_format = form.cleaned_data.get("date_format")
                date_format = DATE_FORMAT_CHOICES_PARSE_PARAMS.get(file_date_format).get("date_format")
                
                records_to_create = []
                
                # delete all existing data for the city and parameters
                DataValue.objects.filter(city=city, parameter__in=parameters).delete()
                
                for value in data:
                    date_str = str(value.get("date"))
                    date_val = datetime.datetime.strptime(date_str, date_format).date()
                    
                    for parameter in parameters:
                        if value.get(parameter.slug):
                            val = value.get(parameter.slug)
                            record_data = {"date": date_val, "city": city, "parameter": parameter, "value": val}
                            records_to_create.append({**record_data})
                
                # bulk create. Saves database round trips
                try:
                    # create
                    if records_to_create:
                        DataValue.objects.bulk_create(
                            [DataValue(**values) for values in records_to_create], batch_size=1000
                        )
                except Exception as e:
                    form.add_error(None, f"An error occurred while saving data. {str(e)}")
                    context.update({"form": form})
                    return render(request, template_name=template, context=context)
                
                messages.success(request, "Data loaded successfully")
                return redirect(reverse("cityclimate_data_checklist", args=(page.pk,)))
            
            except Exception as e:
                form.add_error(None, f"An error occurred while processing data. {str(e)}")
                context.update({"form": form})
                return render(request, template_name=template, context=context)
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


def view_city_climate_data(request, page_id, city_id):
    page = get_object_or_404(CityClimateDataPage, pk=page_id).specific
    city = get_object_or_404(City, pk=city_id)
    
    parameters = page.data_parameters.all()
    page_data = get_climatology_page_data(page, city_id, date_as_str=False, param_key_field="id", params_as_dict=True)
    
    context = {
        "page": page,
        "city": city,
        "parameters": parameters,
        "page_data_values": page_data,
        "header_str": f"Uploaded Data for {city.name}",
        "template_date_format": page.template_date_format,
        "delete_url": reverse("confirm_delete_city_climate_data", args=[page_id, city_id]),
        "index_url": reverse("cityclimate_data_checklist", args=[page_id]),
        "update_url": reverse("cityclimate_load_data", args=[page_id, city_id])
    }
    
    return render(request, "cityclimate/view_city_climate_data.html", context)


def confirm_delete_city_climate_data(request, page_id, city_id):
    page = get_object_or_404(CityClimateDataPage, pk=page_id)
    
    city = get_object_or_404(City, pk=city_id)
    
    context = {
        "header_str": "Delete Data for {}".format(city.name),
        "city": city,
        "page": page.specific,
        "delete_url": reverse("delete_city_climate_date", args=[page_id, city.id]),
        "index_url": reverse("cityclimate_data_checklist", args=[page_id])
    }
    
    return render(request, "cityclimate/confirm_delete_city_climate_data.html", context)


def delete_city_climate_date(request, page_id, city_id):
    if request.method == "GET":
        return redirect(reverse("cityclimate_data_checklist", args=(page_id,)))
    
    city_id = get_object_or_404(City, pk=city_id)
    
    page = CityClimateDataPage.objects.filter(pk=page_id)
    
    if page.exists():
        page = page.first().specific
    
    parameters = page.data_parameters.all()
    
    DataValue.objects.filter(city_id=city_id, parameter__in=parameters).delete()
    
    messages.success(request, "Data deleted successfully")
    
    return redirect(reverse("cityclimate_data_checklist", args=(page_id,)))


def climate_data(request, page_id):
    city_id = request.GET.get("city_id")
    
    page = CityClimateDataPage.objects.filter(pk=page_id)
    
    if page.exists():
        page = page.first().specific
    
    page_data = get_climatology_page_data(page, city_id, date_as_str=False)
    
    return JsonResponse(page_data, safe=False)
