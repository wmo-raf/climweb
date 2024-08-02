from datetime import datetime,timedelta
from django.utils import timezone

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.gis.geos import Point

from pages.aviation.models import Airport,Message,AirportCategory
from pages.aviation.forms import AirportLoaderForm, MessageForm
from pages.aviation.decode import identify_message_type, parse_metar_message,parse_taf_message

# views.py
from django.http import JsonResponse



def add_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg_encode = form.cleaned_data['msg_encode']
            
            # Split messages by comma and decode them
            raw_messages = msg_encode.strip().split(',')
            data_to_save = []
            airport_ids_not_found = set()
            
            warnings = []

            for message in raw_messages:
                if identify_message_type(message)=="METAR":
                    decoded_message, message_warnings = parse_metar_message(message)
                    if message_warnings:
                        warnings.extend([f"{warning} for {decoded_message}"  for warning in message_warnings])
                        continue

                    if decoded_message:
                        airport_code = decoded_message.get('airport')
                        if airport_code:
                           
                            airport = Airport.objects.filter(id=airport_code).first()
                            if airport:
                                # Prepare data for saving or updating
                                data = {
                                    'airport': airport,
                                    'msg_encode': message,
                                    'msg_decode': decoded_message,
                                    'msg_format': decoded_message.get('type'),
                                    'msg_datetime': datetime.strptime(decoded_message.get('datetime'),'%Y-%m-%d %H:%M:%S UTC')
                                }

                                data_to_save.append(data)
                                
                                
                            else:
                                airport_ids_not_found.add(airport_code)

               
                elif identify_message_type(message)=="TAF":
                    decoded_message, message_warnings = parse_taf_message(message)
                    if message_warnings:
                        warnings.extend([f"{warning} for {decoded_message}"  for warning in message_warnings])
                        continue

                    if decoded_message:
                        airport_code = decoded_message.get('airport')
                        if airport_code:
                           
                            airport = Airport.objects.filter(id=airport_code).first()
                            if airport:
                                # Prepare data for saving or updating
                                data = {
                                    'airport': airport,
                                    'msg_encode': message,
                                    'msg_decode': decoded_message,
                                    'msg_format': decoded_message.get('type'),
                                    'msg_datetime': datetime.strptime(decoded_message.get('datetime'),'%Y-%m-%d %H:%M:%S UTC')
                                }

                                data_to_save.append(data)
                                
                                
                            else:
                                airport_ids_not_found.add(airport_code)

                else:
                    decoded_message = {}
                    warnings.append(F"Invalid message format. {message}")
            
            if airport_ids_not_found:
                warnings.append(f"Airport ID(s) not found: {', '.join(airport_ids_not_found)}")
            
            if not data_to_save:
                warnings.append('No valid messages to save.')

            for data in data_to_save:
                Message.objects.update_or_create(
                    airport=data['airport'],
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

    latest_metar_datetime = None
    latest_taf_datetime = None

    if not latest_metar and not latest_taf:
        return JsonResponse({'error': 'No messages found'}, status=404)

    if(latest_metar):
        latest_metar_datetime = latest_metar.msg_datetime.isoformat()
    
    if(latest_taf):
        latest_taf_datetime = latest_taf.msg_datetime.isoformat()

    return JsonResponse({
        'latest_metar_datetime': latest_metar_datetime,
        'latest_taf_datetime': latest_taf_datetime
    })

# Create your views here.
def load_aviation_airports(request):
    template = "aviation/load_airports.html"
    context = {}

    index_url_name = Airport.snippet_viewset.get_url_name("list")
    index_url = reverse(index_url_name)

    if request.POST:
        form = AirportLoaderForm(request.POST, files=request.FILES)

        if form.is_valid():
            airports = form.cleaned_data.get("data")
            overwrite = form.cleaned_data.get("overwrite_existing")

            for airport in airports:

                id = airport.get("id")
                print(id)
                airport_name = airport.get("airport")
                lat = airport.get("lat")
                lon = airport.get("lon")
                category = airport.get("category")
                category_exists = AirportCategory.objects.filter(name__iexact=category).exists()

                airport_exists = Airport.objects.filter(id=id).exists()
                if not category_exists:
                    form.add_error(None, f"Category '{category}' does not exist. "
                                             f"Please check the spelling or add the category first")
                    context.update({"form": form})
                    return render(request, template_name=template, context=context)
                if airport_exists:
                    if not overwrite:
                        form.add_error(None, f"Airport {airport_name} with ID '{id}' already exists. "
                                             f"Please check the overwrite option to update or delete the existing airport.")
                        context.update({"form": form})
                        return render(request, template_name=template, context=context)
                    else:
                        airport_obj = Airport.objects.get(id=id)
                        airport_obj.id = id
                        airport_obj.name = airport_name
                        airport_obj.location = Point(x=lon, y=lat, srid=4326)
                        airport_obj.category = AirportCategory.objects.get(name__iexact=category)
                        print(airport_obj.category)

                        airport_obj.save()
                else:
                    airport_obj = Airport(id=id, name=airport_name, location=Point(x=lon, y=lat, srid=4326), category=AirportCategory.objects.get(name__iexact=category))
                    airport_obj.save()

            return redirect(index_url)
        else:
            context.update({"form": form})
            return render(request, template_name=template, context=context)
        
    form = AirportLoaderForm()
    context.update({"form": form})

    return render(request, template_name=template, context=context)


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
    ).select_related('airport').order_by('-msg_datetime')


    # Construct the response data
    data = {
        'type': 'FeatureCollection',
        'features': [] 
    }

    airport_messages ={}

    for msg in messages:
        airport_id = msg.airport.id
        if airport_id not in airport_messages:
            airport_messages[airport_id] = {
                'id': airport_id,
            }
            data['features'].append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [msg.airport.location.x, msg.airport.location.y],
                },
                'properties':{
                    'id': airport_id,
                    'name': msg.airport.name,
                    'category_name':msg.airport.category.name,
                    'category_color':msg.airport.category.color,
                    'messages':[] 
                }
            })

    for msg in messages:
        for val in data['features']:
            if val['properties']['id'] == msg.airport.id:
                val['properties']['messages'].append({
                    'msg_encode': msg.msg_encode,
                    'msg_datetime': msg.msg_datetime.isoformat(),
                    'msg_decode': msg.msg_decode
                })


    return JsonResponse(data)