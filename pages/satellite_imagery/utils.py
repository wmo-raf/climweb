import xml.etree.ElementTree as ET
from datetime import datetime

import requests
from owslib.wms import WebMapService


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


def extract_domain_values(xml_text, as_string=False):
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

    if as_string:
        dates = [value for value in domain_values]
    else:
        # Parse the values as dates
        date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        dates = [datetime.strptime(value, date_format).timestamp() * 1000 for value in domain_values]
    return dates


def get_layer_time(layer, as_string=False):
    base_url = "https://view.eumetsat.int/geoserver/gwc/service/wmts"
    params = {
        "service": "WMTS",
        "version": "1.0.0",
        "request": "GetDomainValues",
        "tileMatrix": "EPSG:4326",
        "domain": "time",
        "limit": 100,
        "layer": layer,
        "sort": "desc"
    }

    try:
        r = requests.get(base_url, params=params)
        r.raise_for_status()
        values = extract_domain_values(r.text, as_string=as_string)
        return values
    except requests.exceptions.HTTPError as e:
        res = e.response.text

    return None


def get_msg_layer_choices():
    choices = ()
    try:
        layers = get_msg_layers()
        choices = ((layer.get("name"), layer.get("title"),) for layer in layers)
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
