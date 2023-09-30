import textwrap
from io import BytesIO

import cartopy.feature as cf
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont, ImageColor
from cartopy import crs as ccrs
from django.core.files.base import ContentFile

from django.contrib.staticfiles import finders
from geomanager.utils.svg import rasterize_svg_to_png

matplotlib.use('Agg')

fonts = {
    "Roboto-Regular": finders.find("base/fonts/Roboto/Roboto-Regular.ttf"),
    "Roboto-Bold": finders.find("base/fonts/Roboto/Roboto-Bold.ttf")
}

warning_icon = finders.find("cap/images/alert.png")


def cap_geojson_to_image(geojson_feature_collection, extents=None):
    gdf = gpd.GeoDataFrame.from_features(geojson_feature_collection)

    width = 2
    height = 2

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


def generate_cap_alert_card_image(area_map_img_buffer, cap_detail, file_name):
    out_img_width = 800
    out_img_height = 800
    padding = 30

    out_img = Image.new(mode="RGBA", size=(out_img_width, out_img_height), color="WHITE")
    draw = ImageDraw.Draw(out_img)

    # add org logo
    org_logo_offset = 10
    max_logo_height = 70
    org_logo_file = cap_detail.get("org_logo_file")
    logo_h = 0
    if org_logo_file:
        logo_image = Image.open(org_logo_file)
        logo_w, logo_h = logo_image.size
        if logo_h > max_logo_height:
            ratio = logo_w / logo_h
            new_width = int(ratio * max_logo_height)
            logo_image = logo_image.resize((new_width, max_logo_height))
            logo_w, logo_h = logo_image.size

        offset = ((out_img_width - logo_w) // 2, org_logo_offset)
        out_img.paste(logo_image, offset, logo_image)

    # add alert title
    title_font_size = 20
    text_max_width = int(out_img_width * 0.07)
    title_top_offset = org_logo_offset + logo_h + padding
    title_h = 0
    title = cap_detail.get("title")
    roboto_bold_font_path = fonts.get("Roboto-Bold")
    font = None
    if roboto_bold_font_path:
        font = ImageFont.truetype(roboto_bold_font_path, title_font_size)
        wrapper = textwrap.TextWrapper(width=text_max_width)
        word_list = wrapper.wrap(text=title)
        title_new = ''
        for ii in word_list:
            title_new = title_new + ii + '\n'
        _, _, title_w, title_h = draw.textbbox((0, 0), title_new, font=font)
        draw.text(((out_img_width - title_w) / 2, title_top_offset), title_new, font=font, fill="black")

    # add alert issue time
    issued_date_top_offset = title_top_offset + title_h + padding
    sent = cap_detail.get("properties", {}).get('sent')
    issued_date_text = f"Issued on: {sent}"
    issued_date_h = 0
    if font:
        _, _, issued_date_w, issued_date_h = draw.textbbox((0, 0), issued_date_text, font=font)
        draw.text(((out_img_width - issued_date_w) / 2, issued_date_top_offset), issued_date_text, font=font,
                  fill="black")

    # paste alert image
    map_image_top_offset = issued_date_top_offset + issued_date_h + padding
    map_image = Image.open(area_map_img_buffer)
    map_image_w, map_image_h = map_image.size
    map_offset = (padding, map_image_top_offset)
    out_img.paste(map_image, map_offset)

    # add alert badge
    alert_badge_height = 50
    ulx = padding + map_image_w + padding
    uly = map_image_top_offset + alert_badge_height
    lrx = out_img_width - padding
    lry = map_image_top_offset

    severity_background_color = cap_detail.get("severity").get("background_color")
    severity_border_color = cap_detail.get("severity").get("border_color")
    severity_icon_color = cap_detail.get("severity").get("icon_color")
    severity_color = cap_detail.get("severity").get("color")

    badge_bg_color = ImageColor.getrgb(severity_background_color)
    badge_border_color = ImageColor.getrgb(severity_border_color)

    draw.rectangle((ulx, uly, lrx, lry), fill=badge_bg_color, outline=badge_border_color)

    event_icon = cap_detail.get("properties").get("event_icon")
    if not event_icon:
        event_icon = "alert"

    max_icon_height = 30

    try:
        icon_file = rasterize_svg_to_png(icon_name=event_icon, fill_color=severity_icon_color)
    except Exception:
        icon_file = warning_icon

    event_icon_img = Image.open(icon_file, formats=["PNG"])
    icon_w, icon_h = event_icon_img.size
    if logo_h > max_icon_height:
        icon_ratio = icon_w / icon_h
        new_icon_width = int(icon_ratio * max_icon_height)
        event_icon_img = event_icon_img.resize((new_icon_width, max_icon_height))
        icon_w, icon_h = event_icon_img.size

    badge_width = out_img_width - ulx - padding
    rec_width = 40
    rec_padding = 5

    icon_ulx = ulx + rec_padding
    icon_uly = uly - rec_padding
    icon_lrx = lrx - (badge_width - (rec_width + rec_padding))
    icon_lry = lry + rec_padding

    icon_rect_fill_color = ImageColor.getrgb(severity_color)
    draw.rectangle((icon_ulx, icon_uly, icon_lrx, icon_lry), fill=icon_rect_fill_color, outline=badge_border_color)

    event_icon_offset = (
        padding + map_image_w + padding + (rec_padding * 2), map_image_top_offset + (rec_padding * 2))

    out_img.paste(event_icon_img, event_icon_offset, event_icon_img)

    buffer = BytesIO()
    out_img.convert("RGB").save(fp=buffer, format='PNG')
    buff_val = buffer.getvalue()
    return ContentFile(buff_val, file_name)
