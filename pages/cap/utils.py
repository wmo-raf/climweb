import os
from io import BytesIO

import cartopy.feature as cf
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
from cartopy import crs as ccrs
from django.conf import settings
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg

matplotlib.use('Agg')


def cap_geojson_to_image(geojson_feature_collection, options, extents=None):
    gdf = gpd.GeoDataFrame.from_features(geojson_feature_collection)

    height = 3.6
    width = 3.6

    fig = plt.figure(figsize=(width, height))
    # ax = plt.axes([0, 0, 1, 1], projection=ccrs.PlateCarree())
    ax = plt.subplot(1, 1, 1, projection=ccrs.PlateCarree())

    # set line width
    [x.set_linewidth(0.2) for x in ax.spines.values()]

    # set extent
    # if extents:
    #     ax.set_extent(extents, crs=ccrs.PlateCarree())

    # add country borders
    ax.add_feature(cf.LAND)
    ax.add_feature(cf.OCEAN)
    ax.add_feature(cf.BORDERS, linewidth=0.1, linestyle='-', alpha=1)

    # Plot the GeoDataFrame using the plot() method
    gdf.plot(ax=ax, color=gdf["severity_color"], edgecolor='#333', linewidth=0.3, legend=True)
    # label areas
    gdf.apply(lambda x: ax.annotate(text=x["areaDesc"], xy=x.geometry.centroid.coords[0], ha='center', fontsize=7),
              axis=1)

    # add logo
    if options.get("org_logo"):
        logo_file = options.get("org_logo").file.path
        logo_path = os.path.join(settings.MEDIA_ROOT, logo_file)
        logo_img = mpimg.imread(logo_path)
        logo = OffsetImage(logo_img, zoom=0.1)
        logo_position = (0.5, 0.5)
        logo_box = AnnotationBbox(logo,
                                  logo_position,
                                  xycoords='axes fraction',
                                  box_alignment=(0, 0),
                                  pad=0,
                                  frameon=False)
        ax.add_artist(logo_box)

        # add title
    if options.get("title"):
        plt.title(options.get("title"), fontsize=8)

    # create plot
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches="tight", pad_inches=0.2, dpi=200)

    # close plot
    plt.close()

    return buffer
