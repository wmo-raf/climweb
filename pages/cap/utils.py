from django.utils.translation import gettext as _

from base.models import ImportantPages


def create_cap_geomanager_dataset(cap_geomanager_settings, has_live_alerts, request=None):
    sub_category = cap_geomanager_settings.geomanager_subcategory

    more_info = None

    if request:
        important_pages = ImportantPages.for_request(request)
        if important_pages.cap_warnings_list_page:
            more_info = {
                "linkText": _("Go to warnings list"),
                "linkUrl": important_pages.cap_warnings_list_page.get_full_url(request),
                "isButton": True,
                "showArrow": True
            }

    if not sub_category:
        return None

    title = cap_geomanager_settings.layer_title
    metadata = cap_geomanager_settings.geomanager_layer_metadata
    auto_refresh_interval = cap_geomanager_settings.auto_refresh_interval

    # convert to milliseconds
    if auto_refresh_interval:
        auto_refresh_interval = auto_refresh_interval * 60 * 1000

    cap_geojson_url = cap_geomanager_settings.get_cap_geojson_url(request)

    dataset_id = "cap_alerts"

    dataset = {
        "id": dataset_id,
        "dataset": dataset_id,
        "name": title,
        "isCapAlert": True,
        "capConfig": {
            "baseUrl": cap_geojson_url,
            "refreshInterval": auto_refresh_interval
        },
        "initialVisible": has_live_alerts,
        "layer": dataset_id,
        "category": sub_category.category.pk,
        "sub_category": sub_category.pk,
        "public": True,
        "layers": []
    }

    if metadata:
        dataset.update({"metadata": metadata.pk})

    layer = {
        "id": dataset_id,
        "dataset": dataset_id,
        "name": title,
        "layerConfig": {
            "type": "vector",
            "source": {
                "type": "geojson",
                "data": {"type": "FeatureCollection", "features": []},
            },
            "render": {
                "layers": [
                    {
                        "type": "fill",
                        "metadata": {
                            "position": "top",
                        },
                        "paint": {
                            "fill-color": [
                                "match",
                                ["get", "severity"],
                                "Extreme",
                                "#d72f2a",
                                "Severe",
                                "#fe9900",
                                "Moderate",
                                "#ffff00",
                                "Minor",
                                "#03ffff",
                                "#3366ff",
                            ],
                            "fill-opacity": 1,
                        },
                        "filter": [
                            "in",
                            ["get", "severity"],
                            ["literal", ["Extreme", "Severe", "Moderate", "Minor"]],
                        ],
                    },
                    {
                        "type": "line",
                        "metadata": {
                            "position": "top",
                        },
                        "paint": {
                            "line-color": [
                                "match",
                                ["get", "severity"],
                                "Extreme",
                                "#ac2420",
                                "Severe",
                                "#ca7a00",
                                "Moderate",
                                "#cbcb00",
                                "Minor",
                                "#00cdcd",
                                "#003df4",
                            ],
                            "line-width": 0.1,
                        },
                        "filter": [
                            "in",
                            ["get", "severity"],
                            ["literal", ["Extreme", "Severe", "Moderate", "Minor"]],
                        ],
                    },
                ]
            },
        },
        "layerFilterParams": {
            "severity": [
                {"label": "Extreme", "value": "Extreme"},
                {"label": "Severe", "value": "Severe"},
                {"label": "Moderate", "value": "Moderate"},
                {"label": "Minor", "value": "Minor"},
            ],
        },
        "layerFilterParamsConfig": [
            {
                "isMulti": True,
                "type": "checkbox",
                "key": "severity",
                "required": "true",
                "default": [
                    {"label": "Extreme", "value": "Extreme"},
                    {"label": "Severe", "value": "Severe"},
                    {"label": "Moderate", "value": "Moderate"},
                ],
                "sentence": "Filter by Severity {selector}",
                "options": [
                    {"label": "Extreme", "value": "Extreme"},
                    {"label": "Severe", "value": "Severe"},
                    {"label": "Moderate", "value": "Moderate"},
                    {"label": "Minor", "value": "Minor"},
                    {"label": "Unknown", "value": "Unknown"},
                ],
            },
        ],
        "legendConfig": {
            "items": [
                {
                    "color": "#d72f2a",
                    "name": "Extreme Severity",
                },
                {
                    "color": "#fe9900",
                    "name": "Severe Severity",
                },
                {
                    "color": "#ffff00",
                    "name": "Moderate Severity",
                },
                {
                    "color": "#03ffff",
                    "name": "Minor Severity",
                },
                {
                    "color": "#3366ff",
                    "name": "Unknown Severity",
                },
            ],
            "type": "basic",
        },
        "interactionConfig": {
            "capAlert": True,
            "type": "intersection",
        },
    }

    if more_info:
        layer["moreInfo"] = more_info

    dataset["layers"].append(layer)

    return dataset
