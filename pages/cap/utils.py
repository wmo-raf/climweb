from io import BytesIO

import cartopy.feature as cf
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
from cartopy import crs as ccrs

matplotlib.use('Agg')


def cap_geojson_to_image(geojson_feature_collection, options, extents=None):
    gdf = gpd.GeoDataFrame.from_features(geojson_feature_collection)

    height = 3.6
    width = 3.6

    fig = plt.figure(figsize=(width, height))
    ax = plt.axes([0, 0, 1, 1], projection=ccrs.PlateCarree())

    # set line width
    [x.set_linewidth(0.2) for x in ax.spines.values()]

    # set extent
    if extents:
        ax.set_extent(extents, crs=ccrs.PlateCarree())

    # add country borders
    ax.add_feature(cf.LAND)
    ax.add_feature(cf.OCEAN)
    ax.add_feature(cf.BORDERS, linewidth=0.1, linestyle='-', alpha=1)

    # Plot the GeoDataFrame using the plot() method
    gdf.plot(ax=ax, color=gdf["severity_color"], edgecolor='#333', linewidth=0.3, legend=True)
    # label areas
    gdf.apply(lambda x: ax.annotate(text=x["areaDesc"], xy=x.geometry.centroid.coords[0], ha='center', fontsize=7),
              axis=1)

    # add title
    if options.get("title"):
        plt.title(options.get("title"), fontsize=9)

    # create plot
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches="tight", pad_inches=0.2, dpi=200)

    # close plot
    plt.close()

    return buffer


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
