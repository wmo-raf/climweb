import glob
import xml.etree.ElementTree as ET
from datetime import datetime
from io import BytesIO

import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib
import matplotlib.pyplot as plt
import requests
from PIL import Image
from dateutil.parser import parse as parsedate
from owslib.wms import WebMapService

matplotlib.use('Agg')


def get_msg_layers():
    base_url = "https://view.eumetsat.int/geoserver/wms?request=GetCapabilities&service=WMS&version=1.1.1"
    wms = WebMapService(base_url, version='1.1.1')

    wms_layers = list(wms.contents)
    layers = []

    for layer in wms_layers:
        if layer.startswith("msg_"):
            title = wms[layer].title
            layers.append({"title": title, "name": layer})
    return layers


def extract_domain_values(xml_text, as_timestamp=True):
    # Parse the XML
    root = ET.fromstring(xml_text)

    # Define the XML namespaces
    namespaces = {
        'ows': 'http://www.opengis.net/ows/1.1',
        'default': 'http://demo.geo-solutions.it/share/wmts-multidim/wmts_multi_dimensional.xsd'
    }

    # Find the Domain element
    domain_element = root.find('default:Domain', namespaces)

    # Extract the domain values
    domain_values = domain_element.text.split(',')

    values = []

    for value in domain_values:
        date = parsedate(value)

        if as_timestamp:
            date = date.timestamp() * 1000
        values.append(date)

    return sorted(values)


def get_layer_time(layer, as_timestamp=True):
    base_url = "https://view.eumetsat.int/geoserver/gwc/service/wmts"
    params = {
        "service": "WMTS",
        "version": "1.0.0",
        "request": "GetDomainValues",
        "tileMatrix": "EPSG:4326",
        "domain": "time",
        "limit": 200,
        "layer": layer,
        "sort": "desc"
    }

    try:
        r = requests.get(base_url, params=params)
        r.raise_for_status()
        values = extract_domain_values(r.text, as_timestamp=as_timestamp)
        return values
    except requests.exceptions.HTTPError as e:
        res = e.response.text
        print(res)
        return None


def get_msg_layer_choices():
    choices = []
    try:
        layers = get_msg_layers()
        choices = [(layer.get("name"), layer.get("title"),) for layer in layers]
    except Exception:
        pass
    return choices


def get_msg_layer_title(layer_name):
    layers = get_msg_layers()
    if layers:
        for layer in layers:
            if layer.get("name") == layer_name:
                return layer.get("title")
    return None


def get_msg_layer_details(layer_name):
    parts = layer_name.split(":")
    layer_name = layer_name.replace(":", "/")
    base_url = f"https://view.eumetsat.int/geoserver/{layer_name}/ows?service=WMS&version=1.3.0&request=GetCapabilities"

    wms = WebMapService(base_url, version='1.1.1')

    layer = wms[parts[1]]
    title = layer.title
    abstract = layer.abstract

    return {"title": title, "abstract": abstract}


def get_wms_map(layer_name, time, extent=None):
    height = 5.12
    width = 5.12

    fig = plt.figure(figsize=(width, height))
    ax = plt.axes([0, 0, 1, 1], projection=ccrs.PlateCarree())

    # set extentZ
    if extent:
        ax.set_extent(extent, crs=ccrs.PlateCarree())

    # add country borders
    ax.add_feature(cf.BORDERS, linestyle='-', alpha=1)

    date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    date = datetime.strptime(time, date_format)

    wms_kwargs = {
        "time": time,
        "height": 512,
        "width": 512
    }

    ax.add_wms(wms="https://view.eumetsat.int/geoserver/wms", layers=[layer_name], wms_kwargs=wms_kwargs)

    fontsize = 9

    date_str = f"{date.strftime('UTC %Y-%m-%d %H:%M')}"

    ax.text(0.02, 0.02, "EUMETSAT", ha='left', va='bottom', transform=ax.transAxes,
            fontsize=fontsize, bbox=dict(facecolor='black', alpha=0.5, edgecolor='none', boxstyle='square,pad=0.3'),
            color='white')

    ax.text(0.98, 0.02, date_str, ha='right', va='bottom', transform=ax.transAxes,
            fontsize=fontsize, bbox=dict(facecolor='black', alpha=0.5, edgecolor='none', boxstyle='square,pad=0.3'),
            color='white')

    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches="tight", pad_inches=0, dpi=200)

    # close plot
    plt.close()

    return buffer


def create_gif(input_path, output_file, duration=200):
    frames = []
    # Get a list of all image files based on the provided pattern
    image_files = glob.glob(f"{input_path}/*.png")

    # Sort the image files to ensure they are in the correct sequence
    image_files.sort()

    for image_file in image_files:
        img = Image.open(image_file)
        frames.append(img)

    # Save the frames as a GIF
    frames[0].save(f"{output_file}.gif", format='GIF', append_images=frames[1:], save_all=True, duration=duration,
                   loop=0)


def get_anim_upload_path(instance):
    layer_slug = instance.layer_slug
    today = datetime.today().strftime("%Y%m%d")
    return f"satellite-imagery/{today}/{layer_slug}"
