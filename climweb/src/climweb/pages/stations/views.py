import tempfile

import requests
from django.conf import settings
from django.db import connection, close_old_connections
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from geomanager.utils.vector_utils import ogr_db_import
from wagtail.admin import messages
from wagtail.admin.auth import user_passes_test, user_has_any_page_permission
from wagtail.api.v2.utils import get_full_url
from wagtailcache.cache import clear_cache, cache_page

from climweb.base.models import OrganisationSetting
from .forms import StationsUploadForm, StationColumnsForm
from .models import StationSettings

OSCAR_API_URL = "https://oscar.wmo.int/surface/rest/api/search/station"

# data_type values must match keys in geomanager's POSTGRES_DATA_TYPES_DJANGO_FIELDS_MAPPING
OSCAR_STATION_COLUMNS = [
    {"name": "gid", "label": "ID", "data_type": "integer", "table": False, "popup": False},
    {"name": "name", "label": "Station Name", "data_type": "character varying", "table": True, "popup": True},
    {"name": "wigos_id", "label": "WIGOS ID", "data_type": "character varying", "table": True, "popup": True},
    {"name": "elevation", "label": "Elevation (m)", "data_type": "double precision", "table": False, "popup": True},
    {"name": "station_type", "label": "Station Type", "data_type": "character varying", "table": False, "popup": True},
    {"name": "operating_status", "label": "Declared Status", "data_type": "character varying", "table": False, "popup": True},
]


def _fetch_oscar_stations(country_code):
    """Fetch all stations for a country from the OSCAR Surface API, handling pagination."""
    params = {"territoryName": country_code, "page": 1}

    response = requests.get(OSCAR_API_URL, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()

    stations = data.get("stationSearchResults", [])
    pageCount = data.get("pageCount", 1)

    page = 1
    while page < pageCount:
        params["page"] = page
        r = requests.get(OSCAR_API_URL, params=params, timeout=60)
        r.raise_for_status()
        batch = r.json().get("stationSearchResults", [])
        if not batch:
            break
        stations.extend(batch)
        page += 1

    return stations


def _create_oscar_stations_table(stations, station_settings):
    """Drop and recreate the stations table, then insert OSCAR station records."""
    table_name = station_settings.full_table_name

    with connection.cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                gid              SERIAL PRIMARY KEY,
                name             VARCHAR(255),
                wigos_id         VARCHAR(100),
                elevation        DOUBLE PRECISION,
                station_type     VARCHAR(100),
                operating_status VARCHAR(100),
                geom             GEOMETRY(Point, 4326)
            )
        """)
        cursor.execute(f"CREATE INDEX ON {table_name} USING GIST (geom)")

        for station in stations:
            lon = station.get("longitude")
            lat = station.get("latitude")
            if lon is None or lat is None:
                continue
            cursor.execute(
                f"""
                INSERT INTO {table_name}
                    (name, wigos_id, elevation, station_type, operating_status, geom)
                VALUES (%s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                """,
                [
                    station.get("name"),
                    station.get("wigosId"),
                    station.get("elevation"),
                    station.get("stationTypeName"),
                    station.get("declaredStatus"),
                    lon,
                    lat,
                ],
            )


@user_passes_test(user_has_any_page_permission)
def load_stations(request):
    template = "stations/stations_upload.html"

    context = {}
    station_settings = StationSettings.for_request(request)

    if request.POST:
        form = StationsUploadForm(request.POST, request.FILES)

        if form.is_valid():
            shp_zip = form.cleaned_data.get("shp_zip")

            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{shp_zip.name}") as temp_file:
                for chunk in shp_zip.chunks():
                    temp_file.write(chunk)

                try:
                    default_db_settings = settings.DATABASES['default']
                    db_params = {
                        "host": default_db_settings.get("HOST"),
                        "port": default_db_settings.get("PORT"),
                        "user": default_db_settings.get("USER"),
                        "password": default_db_settings.get("PASSWORD"),
                        "name": default_db_settings.get("NAME"),
                    }

                    db_settings = {
                        **db_params,
                        "pg_service_schema": station_settings.db_schema
                    }

                    table_info = ogr_db_import(temp_file.name, station_settings.stations_table_name, db_settings,
                                               overwrite=True, validate_geom_types=["Point", "MultiPoint"])

                    columns = table_info.get("properties")
                    geom_type = table_info.get("geom_type")
                    bounds = table_info.get("bounds")

                    # set all columns to show in table and popup
                    for column in columns:
                        column["table"] = False
                        column["popup"] = True

                        # set label to be the name by default
                        column["label"] = column.get("name")

                    # update stations settings
                    station_settings.columns = columns
                    station_settings.geom_type = geom_type
                    station_settings.bounds = bounds
                    station_settings.name_column = ""
                    station_settings.save()

                except Exception as e:
                    form.add_error(None, str(e))
                    context.update({"form": form})
                    return render(request, template_name=template, context=context)

            messages.success(request, _("Stations data loaded successfully"))

            # clear wagtail cache
            clear_cache()

            return redirect(reverse("preview_stations"))
        else:
            context.update({"form": form})
            return render(request, template_name=template, context=context)
    else:
        form = StationsUploadForm()
        context["form"] = form
        return render(request, template_name=template, context=context)


@user_passes_test(user_has_any_page_permission)
def preview_stations(request):
    template = "stations/stations_preview.html"

    stations_settings = StationSettings.for_request(request)
    stations_vector_tiles_url = get_full_url(request, stations_settings.stations_vector_tiles_url)

    context = {
        "mapConfig": {
            "stationBounds": stations_settings.bounds,
            "stationsVectorTilesUrl": stations_vector_tiles_url,
        },
        "load_stations_url": reverse("load_stations"),
    }

    if stations_settings.columns:
        context.update({"station_columns": stations_settings.columns})

    initial_data = {
        "columns": stations_settings.columns,
        "name_column": stations_settings.name_column
    }

    column_choices = [(column, column) for column in stations_settings.station_columns_list]

    if request.POST:
        form = StationColumnsForm(request.POST, initial=initial_data, column_choices=column_choices)
        if form.is_valid():
            columns = form.cleaned_data.get("columns")
            name_column = form.cleaned_data.get("name_column")

            if columns:
                stations_settings.columns = columns
                stations_settings.name_column = name_column
                stations_settings.save()
                # clear wagtail cache
                clear_cache()
            messages.success(request, _("Stations columns updated successfully"))

            # redirect
            return redirect(reverse("preview_stations"))
        else:
            context.update({"form": form})
            return render(request, template_name=template, context=context)
    else:
        form = StationColumnsForm(initial=initial_data, column_choices=column_choices)
        context["form"] = form

    return render(request, template, context=context)


@user_passes_test(user_has_any_page_permission)
def sync_stations_from_oscar(request):
    if request.method != "POST":
        return redirect(reverse("load_stations"))

    station_settings = StationSettings.for_request(request)
    org_settings = OrganisationSetting.for_request(request)
    country_code = org_settings.country

    if not country_code:
        messages.error(
            request,
            _("No country set in Organisation Settings. Please configure it before syncing."),
        )
        return redirect(reverse("preview_stations"))

    try:
        stations = _fetch_oscar_stations(country_code)
    except requests.exceptions.RequestException as e:
        messages.error(request, _("Failed to reach OSCAR Surface API: {}").format(str(e)))
        return redirect(reverse("preview_stations"))

    if not stations:
        messages.warning(
            request,
            _("No stations returned from OSCAR Surface for country code: {}").format(country_code),
        )
        return redirect(reverse("preview_stations"))

    try:
        _create_oscar_stations_table(stations, station_settings)
    except Exception as e:
        messages.error(request, _("Error saving station data: {}").format(str(e)))
        return redirect(reverse("preview_stations"))

    lons = [s["longitude"] for s in stations if s.get("longitude") is not None]
    lats = [s["latitude"] for s in stations if s.get("latitude") is not None]
    bounds = [min(lons), min(lats), max(lons), max(lats)] if lons and lats else None

    station_settings.columns = OSCAR_STATION_COLUMNS
    station_settings.geom_type = "Point"
    station_settings.name_column = "name"
    if bounds:
        station_settings.bounds = bounds
    station_settings.save()

    clear_cache()

    messages.success(
        request,
        _("{count} stations synced from OSCAR Surface (country: {code}).").format(
            count=len(stations), code=country_code
        ),
    )
    return redirect(reverse("preview_stations"))


@method_decorator(cache_page, name='get')
class StationsTileView(View):
    def get(self, request, z, x, y):
        station_settings = StationSettings.for_request(request)

        sql = f"""WITH
            bounds AS (
              SELECT ST_TileEnvelope({z}, {x}, {y}) AS geom
            ),
            mvtgeom AS (
              SELECT ST_AsMVTGeom(ST_Transform(t.geom, 3857), bounds.geom) AS geom,
                *
              FROM {station_settings.full_table_name} t, bounds
              WHERE ST_Intersects(ST_Transform(t.geom, 4326), ST_Transform(bounds.geom, 4326))
            )
            SELECT ST_AsMVT(mvtgeom, 'default') FROM mvtgeom;
            """

        close_old_connections()
        with connection.cursor() as cursor:
            cursor.execute(sql)
            tile = cursor.fetchone()[0]
            if not len(tile):
                raise Http404()

        return HttpResponse(tile, content_type="application/x-protobuf")
