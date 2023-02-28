from django.contrib.gis.geos import GEOSGeometry
import json
from site_settings.models import Country

with open('/Users/grace/Projects/WMO/nmhs_cms/site_settings/data/africa_countries.geojson') as f:
    data = json.load(f)

for feature in data['features']:
    name = feature['properties']['name']
    iso = feature['properties']['iso3']
    size = feature['properties']['size']
    print("Country: ",name)
    geom = GEOSGeometry(json.dumps(feature['geometry']))
    country = Country(name=name, geom=geom, iso=iso, size=size)
    country.save()