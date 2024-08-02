from datetime import datetime, timedelta, time

from metar_taf_parser.parser.parser import TAFParser,MetarParser
from metar_taf_parser.model.enum import CloudQuantity, CloudType, WeatherChangeType, Phenomenon,Intensity, Descriptive
from metar_taf_parser.model.model import WeatherCondition, WeatherChangeType


CLOUD_COVERAGE = {
        "SKC": "Sky Clear",
        "FEW": "Few clouds",
        "SCT": "Scattered clouds",
        "BKN": "Broken clouds",
        "OVC": "Overcast"
}
# Get the current date
current_date = datetime.now()

def fmt_date(day, time):
    print(day, type(time))
    print(day, time)
    # Replace the day, hour, and minute in the current date
    data_date = current_date.replace(day=day, hour=time.hour, minute=time.minute, second=time.second, microsecond=0)
        # Adjust for month wrap-around
    if data_date > current_date + timedelta(days=1):
        data_date = data_date - timedelta(days=current_date.day)

    

    return data_date

def parse_metar_message(message):
    try:
        metar = MetarParser().parse(message)
        wind = metar._get_wind()
        clouds = metar._get_clouds()
        visibility = metar._get_visibility()
         

        metar_date = fmt_date(metar.day, metar.time)

        decoded_message = {
            "type": "METAR",
            "airport": metar.station,
            "datetime": metar_date.strftime('%Y-%m-%d %H:%M:%S UTC'),
            "temperature":{
                "value":metar.temperature if metar.temperature else None,
                "units":"celsius"
            },
            "dew_point":{
                "value":metar.dew_point if metar.dew_point else None,
                "units":"celsius"
            },
            "altimeter":{
                "value":metar.altimeter if metar.altimeter else None,
                "units":"celsius"
            },
            "winds": {
                "direction": {
                    "value":wind.direction if wind else None,
                    "units":""
                },
                "degrees": {
                    "value":wind.degrees if wind else None,
                    "units":"degrees"
                },
                "gust": {
                    "value":wind.gust if wind else None,
                    "units":wind.unit  if wind else None
                },
                "min_variation": {
                    "value":wind.min_variation if wind else None,
                    "units":"degrees"
                },
                "max_variation": {
                    "value":wind.max_variation if wind else None,
                    "units":"degrees"
                },
                "speed": {
                    "value":wind.speed if wind else None,
                    "units":wind.unit if wind else None
                }
            },
            "clouds": [{
                "quantity": {
                    "value":CloudQuantity(cloud.quantity.value).__repr__() if cloud.quantity else None, 
                    "units":""
                },
                "type": {
                    "value":CloudType(cloud.type.value).__repr__() if cloud.type is not None else None, 
                    "units":""
                },
                "height":{
                    "value": cloud.height if cloud.height else None,
                    "units":"feet"
                }
        } for cloud in clouds] if clouds else [],
            "visibility":{
                "distance":{
                    "value":visibility.distance if visibility else None,
                    "units":"meters/nauticle miles"
                },
                "min_distance":{
                    "value":visibility.min_distance if visibility else None,
                    "units":"meters"
                },
                "min_direction":{
                    "value":visibility.min_direction  if visibility else None,
                    "units":""
                }
            }
        
        }
        
        warnings = []
    except Exception as e:
        decoded_message = {}
        warnings = [str(e)]
    
    return decoded_message, warnings

def parse_taf_message(message):
    try:
        taf = TAFParser().parse(message)
        wind = taf._get_wind()
        clouds = taf._get_clouds()
        turbulence = taf._get_turbulence()
        wind_shear = taf._get_wind_shear()
        visibility = taf._get_visibility()
        trends = taf._get_trends()
        conditions = taf._get_weather_conditions()
        

        taf_date = fmt_date(taf.day, taf.time)

        decoded_message = {
            "type": "TAF",
            "airport": taf.station,
            "datetime": taf_date.strftime('%Y-%m-%d %H:%M:%S UTC'),
            "winds": {
                "direction": {
                    "value":wind.direction if wind else None,
                    "units":""
                },
                "degrees": {
                    "value":wind.degrees if wind else None,
                    "units":"degrees"
                },
                "gust": {
                    "value":wind.gust if wind else None,
                    "units":wind.unit  if wind else None
                },
                "min_variation": {
                    "value":wind.min_variation if wind else None,
                    "units":"degrees"
                },
                "max_variation": {
                    "value":wind.max_variation if wind else None,
                    "units":"degrees"
                },
                "speed": {
                    "value":wind.speed if wind else None,
                    "units":wind.unit if wind else None
                }
            },
            "wind_shear":{
                "height":{
                    "value":wind_shear.height if wind_shear else None,
                    "units":""
                }
            },
            "clouds": [{
                "quantity": {
                    "value":CloudQuantity(cloud.quantity.value).__repr__() if cloud.quantity else None, 
                    "units":""
                },
                "type": {
                    "value":CloudType(cloud.type.value).__repr__() if cloud.type is not None else None, 
                    "units":""
                },
                "height":{
                    "value": cloud.height if cloud.height else None,
                    "units":"feet"
                }
            } for cloud in clouds] if clouds else [],
            "visibility":{
                "distance":{
                    "value":visibility.distance if visibility else None,
                    "units":"meters/nauticle miles"
                },
                "min_distance":{
                    "value":visibility.min_distance if visibility else None,
                    "units":"meters"
                },
                "min_direction":{
                    "value":visibility.min_direction  if visibility else None,
                    "units":""
                }
            },
            "conditions":[{
                "intensity":{
                    "value":Intensity(condition.intensity.value).__repr__(),
                    "units":""
                },
                "descriptive":{
                    "value":Descriptive(condition.descriptive.value).__repr__(),
                    "units":""
                },
                "phenomenons":[{
                    "value":Phenomenon(phenomenon.value).__repr__(),
                    "units":""
                } for phenomenon in condition.phenomenons]}
            for condition in conditions],
            "trends": [
                {
                    "trend_type": WeatherChangeType(trend.type).__repr__() if trend.type else None,
                    "start_date": fmt_date(trend.validity.start_day, time(trend.validity.start_hour, 0, 0)).strftime('%Y-%m-%d %H:%M:%S UTC') if trend._validity  else None,
                    "end_date": fmt_date(trend.validity.end_day, time(trend.validity.end_hour, 0, 0)).strftime('%Y-%m-%d %H:%M:%S UTC') if trend._validity else None,
                    "wind": {
                        "direction": {
                            "value": trend.wind.direction if trend.wind else None,
                            "units": ""
                        },
                        "degrees": {
                            "value": trend.wind.degrees if trend.wind else None,
                            "units": "degrees"
                        },
                        "gust": {
                            "value": trend.wind.gust if trend.wind else None,
                            "units": trend.wind.unit if trend.wind else None
                        },
                        "min_variation": {
                            "value": trend.wind.min_variation if trend.wind else None,
                            "units": "degrees"
                        },
                        "max_variation": {
                            "value": trend.wind.max_variation if trend.wind else None,
                            "units": "degrees"
                        },
                        "speed": {
                            "value": trend.wind.speed if trend.wind else None,
                            "units": trend.wind.unit if trend.wind else None
                        }
                    },
                    "wind_shear": {
                        "height": {
                            "value": trend.wind_shear.height if trend.wind_shear else None,
                            "units": ""
                        }
                    },
                    "clouds": [
                        {
                            "quantity": {
                                "value":CloudQuantity(cloud.quantity.value).__repr__() if cloud.quantity else None, 
                                "units":""
                            },
                            "type": {
                                "value":CloudType(cloud.type.value).__repr__() if cloud.type is not None else None, 
                                "units":""
                            },
                            "height": {
                                "value": cloud.height if cloud.height else None,
                                "units": "feet"
                            }
                        }
                        for cloud in trend.clouds
                    ] if trend.clouds else [],
                    "conditions":[{
                        "intensity":{
                            "value":Intensity(condition.intensity.value).__repr__(),
                            "units":""
                        },
                        "descriptive":{
                            "value":Descriptive(condition.descriptive.value).__repr__(),
                            "units":""
                        },
                        "phenomenons":[{
                            "value":Phenomenon(phenomenon.value).__repr__(),
                            "units":""
                        } for phenomenon in condition.phenomenons]}
                    for condition in trend.weather_conditions] if trend.weather_conditions else [],
                    "visibility": {
                        "distance": {
                            "value": trend.visibility.distance if trend.visibility else None,
                            "units": "meters/nauticle miles"
                        },
                        "min_distance": {
                            "value": trend.visibility.min_distance if trend.visibility else None,
                            "units": "meters"
                        },
                        "min_direction": {
                            "value": trend.visibility.min_direction if trend.visibility else None,
                            "units": ""
                        }
                    }
                }
                if trend else {}
                for trend in trends
            ] if trends else []
        }
        
        warnings = []
    except Exception as e:
        decoded_message = {}
        warnings = [str(e)]
    
    return decoded_message, warnings


def identify_message_type(message):
    # Split the message into lines
    lines = message.strip().splitlines()
    
    # Check if lines is empty
    if not lines:
        return "Unknown"
    
    # Extract the first line and split it
    first_line = lines[0].split()
    
    # Check for TAF or METAR in the first line
    if len(first_line) > 0:
        if "TAF" in first_line[0]:
            return "TAF"
        elif "METAR" in first_line[0] or (len(first_line[0]) == 4 and first_line[0].isalpha() and first_line[0].isupper()):
            return "METAR"
    
    return "Unknown"


def decode_datetime(raw_datetime):
    try:
        date_time = datetime.strptime(raw_datetime, '%d%H%MZ')
        # Ensure it matches the required format
        return date_time.strftime('%Y-%m-%d %H:%M:%S') + 'Z'  # 'Z' denotes UTC
    except ValueError:
        return None
    
def validate_parsed_data(parsed_data, message_type):
    warnings = []
    if parsed_data.get('datetime') is None:
        warnings.append(f"Invalid datetime format in {message_type} message.")
    if parsed_data.get('winds') is None:
        warnings.append(f"Invalid wind format in {message_type} message.")
    return warnings


