import logging
import json

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry
from site_settings.models import Country


# Define the base URL for the Met Norway API
BASE_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
headers = {
  'User-Agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.36'
}

logger = logging.getLogger(__name__)

default_options = () if not hasattr(BaseCommand, 'option_list') \
    else BaseCommand.option_list


class Command(BaseCommand):
    help = ('autotranslate all the message files that have been generated '
            'using the `makemessages` command.')

    def handle(self, *args, **options):
        with open('/home/app/web/nmhs-cms/site_settings/data/countries_extents.geojson') as f:
            data = json.load(f)

        for feature in data['features']:
            name = feature['properties']['name']
            iso = feature['properties']['iso3']
            size = feature['properties']['size']
            print("Country: ",name)
            geom = GEOSGeometry(json.dumps(feature['geometry']))
            country = Country(name=name, geom=geom, iso=iso, size=size)
            country.save()
          

