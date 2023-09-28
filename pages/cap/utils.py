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
