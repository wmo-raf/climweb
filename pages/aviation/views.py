from datetime import datetime,timedelta
from django.utils import timezone

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.gis.geos import Point

from pages.aviation.models import Station,Message, StationCategory
from pages.aviation.forms import StationLoaderForm, MessageForm
from pages.aviation.decode import identify_message_type, parse_metar_message,parse_taf_message
from adminboundarymanager.models import AdminBoundarySettings

# views.py
from django.http import HttpResponse, JsonResponse


def add_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg_encode = form.cleaned_data['msg_encode']
            
            # Split messages by comma and decode them
            raw_messages = msg_encode.strip().split(',')
            data_to_save = []
            station_ids_not_found = set()
            
            warnings = []

            for message in raw_messages:
                if identify_message_type(message)=="METAR":
                    decoded_message, message_warnings = parse_metar_message(message)
                    if message_warnings:
                        warnings.extend([f"{warning} for {decoded_message}"  for warning in message_warnings])
                        continue

                    if decoded_message:
                        station_code = decoded_message.get('station')
                        if station_code:
                           
                            station = Station.objects.filter(id=station_code).first()
                            if station:
                                # Prepare data for saving or updating
                                data = {
                                    'station': station,
                                    'msg_encode': message,
                                    'msg_decode': decoded_message,
                                    'msg_format': decoded_message.get('type'),
                                    'msg_datetime': datetime.strptime(decoded_message.get('datetime'),'%Y-%m-%d %H:%M:%S UTC')
                                }

                                data_to_save.append(data)
                                
                                
                            else:
                                station_ids_not_found.add(station_code)

               
                elif identify_message_type(message)=="TAF":
                    decoded_message, message_warnings = parse_taf_message(message)
                    if message_warnings:
                        warnings.extend([f"{warning} for {decoded_message}"  for warning in message_warnings])
                        continue

                    if decoded_message:
                        station_code = decoded_message.get('station')
                        if station_code:
                           
                            station = Station.objects.filter(id=station_code).first()
                            if station:
                                # Prepare data for saving or updating
                                data = {
                                    'station': station,
                                    'msg_encode': message,
                                    'msg_decode': decoded_message,
                                    'msg_format': decoded_message.get('type'),
                                    'msg_datetime': datetime.strptime(decoded_message.get('datetime'),'%Y-%m-%d %H:%M:%S UTC')
                                }

                                data_to_save.append(data)
                                
                                
                            else:
                                station_ids_not_found.add(station_code)

                else:
                    decoded_message = {}
                    warnings.append(F"Invalid message format. {message}")
            
            if station_ids_not_found:
                warnings.append(f"Station ID(s) not found: {', '.join(station_ids_not_found)}")
            
            if not data_to_save:
                warnings.append('No valid messages to save.')

            for data in data_to_save:
                Message.objects.update_or_create(
                    station=data['station'],
                    msg_format=data['msg_format'],
                    msg_datetime=data['msg_datetime'],
                    defaults={
                        'msg_encode': data['msg_encode'],
                        'msg_decode': data['msg_decode']
                    }
                )
        
            if not warnings:
                success = True
            else:
                success = False

            context = {
                'form': MessageForm() if success else form,
                'warnings': warnings,
                'success': success,
            }

            return render(request, 'aviation/add_message.html', context)
        else:
             # Form errors
            context = {
                'form': form,
                'warnings': form.errors.get_json_data(),
                'success':False
            }
            return render(request, 'aviation/add_message.html', context)
    else:
        form = MessageForm()
    return render(request, 'aviation/add_message.html', {'form': form})

def get_latest_message_datetimes(request):
    latest_metar = Message.objects.filter(msg_format='METAR').order_by('-msg_datetime').first()
    latest_taf = Message.objects.filter(msg_format='TAF').order_by('-msg_datetime').first()
    
    if not latest_metar or not latest_taf:
        return JsonResponse({'error': 'No messages found'}, status=404)

    latest_metar_datetime = latest_metar.msg_datetime
    latest_taf_datetime = latest_taf.msg_datetime
    return JsonResponse({
        'latest_metar_datetime': latest_metar_datetime.isoformat(),
        'latest_taf_datetime': latest_taf_datetime.isoformat()
    })

# Create your views here.
def load_aviation_stations(request):
    template = "aviation/load_stations.html"
    context = {}

    index_url_name = Station.snippet_viewset.get_url_name("list")
    index_url = reverse(index_url_name)

    if request.POST:
        form = StationLoaderForm(request.POST, files=request.FILES)

        if form.is_valid():
            stations = form.cleaned_data.get("data")
            overwrite = form.cleaned_data.get("overwrite_existing")

            for station in stations:
                station_name = station.get("station")
                lat = station.get("lat")
                lon = station.get("lon")
                category = station.get("category")

                exists = Station.objects.filter(name__iexact=station_name).exists()

                if exists:
                    if not overwrite:
                        form.add_error(None, f"Station {station_name} already exists. "
                                             f"Please check the overwrite option to update or delete the existing station.")
                        context.update({"form": form})
                        return render(request, template_name=template, context=context)
                    else:
                        station_obj = Station.objects.get(name__iexact=station_name)
                        station_obj.location = Point(x=lon, y=lat, srid=4326)
                        station_obj.category = category

                        station_obj.save()
                else:
                    station_obj = Station(name=station_name, location=Point(x=lon, y=lat, srid=4326), category=category)
                    station_obj.save()

            return redirect(index_url)
        else:
            context.update({"form": form})
            return render(request, template_name=template, context=context)
        
    form = StationLoaderForm()
    context.update({"form": form})

    return render(request, template_name=template, context=context)



def aviation(request):
    latest_metar_message = Message.objects.filter(msg_format='METAR').order_by('-msg_datetime').first()
    latest_metar_datetime = latest_metar_message.msg_datetime.astimezone(timezone.utc).isoformat() if latest_metar_message else None
    
    print("latest_metar_datetime", latest_metar_datetime)

    abm_settings = AdminBoundarySettings.for_request(request)

    abm_extents = abm_settings.combined_countries_bounds

    stn_categories = StationCategory.objects.all()

    context = {
        'latest_metar_datetime': latest_metar_datetime,
        'bounds':abm_extents,
        'stn_categories':stn_categories
    }
    return render(request, 'aviation/aviation_page.html', context)



def station_data_geojson(request):
    stations = Station.objects.all()
    features = []
    for station in stations:
        # point = GEOSGeometry(station.location)
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': station.coordinates,
            },
            'properties': {
                'id': station.id,
                'name': station.name,
                'category': station.category.name,
            },
        })
    
    data = {
        'type': 'FeatureCollection',
        'features': features,
    }
    return JsonResponse(data)

def get_messages(request):
    msg_format = request.GET.get('format', 'METAR')
    datetime_str = request.GET.get('datetime')
    
    if datetime_str:
        datetime_obj = timezone.datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    else:
        datetime_obj = timezone.now()

    messages = Message.objects.filter(
        msg_format=msg_format,
        msg_datetime__gte=datetime_obj - timedelta(hours=1),
        msg_datetime__lte=datetime_obj
    ).select_related('station')

    print(messages.values().first())
    # Group messages by station
    station_messages = {}
    
    # Construct the response data
    data = {
        'type': 'FeatureCollection',
        'features': [] 
    }

    for msg in messages:
        station_id = msg.station.id
        data['features'].append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [msg.station.location.x, msg.station.location.y],
            },
            'properties':{
                'id': station_id,
                'name': msg.station.name,
                'category_name':msg.station.category.name,
                'category_color':msg.station.category.color,
                'messages':[] 
            }
        })

    for msg in messages:
        for val in data['features']:
            if val['properties']['id'] == msg.station.id:
                val['properties']['messages'].append({
                    'msg_encode': msg.msg_encode,
                    'msg_datetime': msg.msg_datetime.isoformat(),
                    'msg_decode': msg.msg_decode
                })


    return JsonResponse(data)