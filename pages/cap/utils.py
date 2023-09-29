from io import BytesIO

import cartopy.feature as cf
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
from PIL import Image
from cartopy import crs as ccrs
from django.core.files.base import ContentFile

matplotlib.use('Agg')


def cap_geojson_to_image(geojson_feature_collection, extents=None):
    gdf = gpd.GeoDataFrame.from_features(geojson_feature_collection)

    width = 3.5
    height = 3.5

    fig = plt.figure(figsize=(width, height))
    ax = plt.axes([0, 0, 1, 1], projection=ccrs.PlateCarree())

    # set line width
    [x.set_linewidth(0) for x in ax.spines.values()]

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
    gdf.apply(lambda x: ax.annotate(text=x["areaDesc"], xy=x.geometry.centroid.coords[0], ha='center', fontsize=5, ),
              axis=1)

    # create plot
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches="tight", pad_inches=0, dpi=200)

    # close plot
    plt.close()

    return buffer


def generate_cap_summary_image(area_map_img_buffer, cap_detail, file_name):
    width = 800
    height = 800
    out_img = Image.new(mode="RGBA", size=(width, height), color="WHITE")

    map_image = Image.open(area_map_img_buffer)
    map_w, map_h = map_image.size
    offset = ((width - map_w) // 2, 200)
    out_img.paste(map_image, offset)

    org_logo_file = cap_detail.get("org_logo_file")
    if org_logo_file:
        logo_image = Image.open(org_logo_file)
        logo_w, logo_h = logo_image.size
        max_logo_height = 70
        if logo_h > max_logo_height:
            ratio = logo_w / logo_h
            new_width = int(ratio * max_logo_height)
            logo_image = logo_image.resize((new_width, max_logo_height))
            logo_w, logo_h = logo_image.size

        offset = ((width - logo_w) // 2, 10)
        out_img.paste(logo_image, offset, logo_image)

    buffer = BytesIO()
    out_img.convert("RGB").save(fp=buffer, format='PNG')
    buff_val = buffer.getvalue()
    return ContentFile(buff_val, file_name)
