from climweb.pages.cityclimate.models import DataValue


def get_climatology_page_data(page_instance, city_id, date_as_str=False, param_key_field="id", params_as_dict=False):
    parameters = page_instance.data_parameters.all()
    if city_id:
        param_values = DataValue.objects.filter(city_id=city_id, parameter__in=parameters)
    else:
        param_values = DataValue.objects.filter(parameter__in=parameters)
    
    values_dict = {}
    
    for value in param_values:
        date_val = value.date.isoformat() if date_as_str else value.date
        
        param_data = {getattr(value.parameter, param_key_field): value.value}
        
        if not values_dict.get(date_val):
            values_dict[date_val] = {}
        
        if params_as_dict:
            if not values_dict[date_val].get("params_data"):
                values_dict[date_val]["params_data"] = {}
            values_dict[date_val]["params_data"].update(param_data)
        else:
            values_dict[date_val].update(param_data)
        
        values_dict[date_val].update({value.parameter.slug: value.value, "city": value.city.name,
                                      "coordinates": [float(coordinate) for coordinate in value.city.coordinates if
                                                      coordinate]})
    
    values = [{"date": key, **values_dict[key]} for key in values_dict.keys()]
    
    return values
