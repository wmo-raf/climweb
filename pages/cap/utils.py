def create_cap_geomanager_dataset(cap_geomanager_settings, has_live_alerts, request=None):
    sub_category = cap_geomanager_settings.geomanager_subcategory

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
                        "type": "fill",
                        "filter": [
                            "in",
                            ["get", "severity"],
                            ["literal", ["Extreme", "Severe", "Moderate", "Minor"]],
                        ],
                    },
                    {
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
                        "type": "line",
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

    dataset["layers"].append(layer)

    return dataset
