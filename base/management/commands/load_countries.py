import json

from django.core.management.base import BaseCommand

from django.contrib.gis.geos import GEOSGeometry

from base.models import Country


class Command(BaseCommand):
    help = ('autotranslate all the message files that have been generated '

            'using the `makemessages` command.')

    def handle(self, *args, **options):
        with open('/home/app/web/nmhs-cms/countries_extents.geojson') as f:
            data = json.load(f)

        for feature in data['features']:
            name = feature['properties']['name']

            iso = feature['properties']['iso3']

            size = feature['properties']['size']

            print("Country: ", name)

            geom = GEOSGeometry(json.dumps(feature['geometry']))

            country = Country(name=name, geom=geom, iso=iso, size=size)

            country.save()
