import textwrap
from io import BytesIO

import cartopy.feature as cf
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont, ImageColor
from cartopy import crs as ccrs
from django.contrib.staticfiles import finders
from django.core.files.base import ContentFile
from geomanager.utils.svg import rasterize_svg_to_png

matplotlib.use('Agg')

fonts = {
    "Roboto-Regular": finders.find("base/fonts/Roboto/Roboto-Regular.ttf"),
    "Roboto-Bold": finders.find("base/fonts/Roboto/Roboto-Bold.ttf")
}

severity_icons = {
    "Extreme": finders.find("cap/images/extreme.png"),
    "Severe": finders.find("cap/images/severe.png"),
    "Moderate": finders.find("cap/images/moderate.png"),
    "Minor": finders.find("cap/images/minor.png"),
}
meta_icons = {
    "urgency": finders.find("cap/images/urgency.png"),
    "certainty": finders.find("cap/images/certainty.png")
}

warning_icon = finders.find("cap/images/alert.png")
area_icon = finders.find("cap/images/area.png")


def cap_geojson_to_image(geojson_feature_collection, extents=None):
    gdf = gpd.GeoDataFrame.from_features(geojson_feature_collection)

    width = 2
    height = 2

    fig = plt.figure(figsize=(width, height))
    ax = plt.axes([0, 0, 1, 1], projection=ccrs.PlateCarree())

    # set line width
    [x.set_linewidth(0) for x in ax.spines.values()]

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
    gdf.apply(lambda x: ax.annotate(text=x["areaDesc"], xy=x.geometry.centroid.coords[0], ha='center', fontsize=5, ),
              axis=1)

    # create plot
    buffer = BytesIO()
    plt.savefig(buffer, format='png', pad_inches=0, dpi=200)

    # close plot
    plt.close()

    return buffer


def generate_cap_alert_card_image(area_map_img_buffer, cap_detail, file_name):
    map_image = Image.open(area_map_img_buffer)
    map_image_w, map_image_h = map_image.size
    standard_map_height = 300
    out_img_width = 800
    out_img_height = 800
    padding = 28

    if map_image_h > standard_map_height:
        out_img_height = out_img_height + (map_image_h - standard_map_height)

    out_img = Image.new(mode="RGBA", size=(out_img_width, out_img_height), color="WHITE")
    draw = ImageDraw.Draw(out_img)

    # add org logo
    org_logo_offset = 10
    max_logo_height = 60
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
    time_fmt = '%d/%m/%Y %H:%M'
    sent = sent.strftime(time_fmt)
    issued_date_text = f"Issued on: {sent} local time"
    issued_date_h = 0
    if font:
        _, _, issued_date_w, issued_date_h = draw.textbbox((0, 0), issued_date_text, font=font)
        draw.text(((out_img_width - issued_date_w) / 2, issued_date_top_offset), issued_date_text, font=font,
                  fill="black")

    # paste alert image
    map_image_top_offset = issued_date_top_offset + issued_date_h + padding
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

    # add alert meta
    meta_h_padding = 10
    urgency_y_offset = uly + padding
    urgency_val = cap_detail.get("properties").get("urgency")
    urgency_icon_file = meta_icons.get("urgency")
    urgency_icon_h = draw_meta_item(out_img, "Urgency", urgency_val, urgency_icon_file, ulx, urgency_y_offset, draw)

    severity_y_offset = urgency_y_offset + meta_h_padding + urgency_icon_h
    severity = cap_detail.get("properties").get("severity")
    severity_icon_file = severity_icons.get(severity)
    severity_icon_h = draw_meta_item(out_img, "Severity", severity, severity_icon_file, ulx, severity_y_offset, draw)

    certainty_y_offset = severity_y_offset + meta_h_padding + severity_icon_h
    certainty = cap_detail.get("properties").get("certainty")
    certainty_icon_file = meta_icons.get("certainty")
    certainty_icon_h = draw_meta_item(out_img, "Certainty", certainty, certainty_icon_file, ulx, certainty_y_offset,
                                      draw)

    # add area of concern
    area_icon_img = Image.open(area_icon)
    area_icon_w, area_icon_h = area_icon_img.size
    area_title_offset_y = certainty_y_offset + certainty_icon_h + padding
    area_title_offset = (ulx, area_title_offset_y)
    out_img.paste(area_icon_img, area_title_offset, area_icon_img)

    font = ImageFont.truetype(roboto_bold_font_path, 16)
    draw.text((ulx + area_icon_w + 5, area_title_offset_y), text="Area of concern", font=font, fill="black")

    areaDesc = cap_detail.get("properties").get("area_desc")
    area_wrapper = textwrap.TextWrapper(width=50)
    area_word_list = area_wrapper.wrap(text=areaDesc)
    area_desc_new = ''
    for ii in area_word_list:
        area_desc_new = area_desc_new + ii + '\n'

    roboto_regular_font_path = fonts.get("Roboto-Regular")
    regular_font = ImageFont.truetype(roboto_regular_font_path, size=12)
    draw.text((ulx + padding, area_title_offset_y + area_icon_h + 1), area_desc_new, font=regular_font, fill="black")

    # add description title
    desc_title = "Description:"
    font = ImageFont.truetype(roboto_bold_font_path, 20)
    _, _, desc_title_w, desc_title_h = draw.textbbox((0, 0), desc_title, font=font)
    desc_title_offset_y = map_image_top_offset + map_image_h + padding
    draw.text((padding, desc_title_offset_y), desc_title, font=font, fill="black")

    # add description text
    description = cap_detail.get("properties").get("description")
    description_wrapper = textwrap.TextWrapper(width=int(out_img_width * 0.16))
    description_word_list = description_wrapper.wrap(text=description)
    description_new = ''
    for ii in description_word_list:
        description_new = description_new + ii + '\n'
    roboto_regular_font_path = fonts.get("Roboto-Regular")
    regular_font = ImageFont.truetype(roboto_regular_font_path, size=12)
    desc_text_offset_y = desc_title_offset_y + desc_title_h + 5
    _, _, desc_text_w, desc_text_h = draw.textbbox((0, 0), description_new, font=regular_font)
    draw.text((padding, desc_text_offset_y), description_new, font=regular_font, fill="black")

    instruction = cap_detail.get("properties").get("instruction")
    if instruction:
        # add description title
        instruction_title = "Instruction:"
        font = ImageFont.truetype(roboto_bold_font_path, 20)
        _, _, instruction_title_w, instruction_title_h = draw.textbbox((0, 0), instruction_title, font=font)
        instruction_title_offset_y = desc_text_offset_y + desc_text_h + padding
        draw.text((padding, instruction_title_offset_y), instruction_title, font=font, fill="black")

        # add instruction text
        instruction_wrapper = textwrap.TextWrapper(width=int(out_img_width * 0.16))
        instruction_word_list = instruction_wrapper.wrap(text=instruction)
        instruction_new = ''
        for ii in instruction_word_list:
            instruction_new = instruction_new + ii + '\n'
        roboto_regular_font_path = fonts.get("Roboto-Regular")
        regular_font = ImageFont.truetype(roboto_regular_font_path, size=12)
        draw.text((padding, instruction_title_offset_y + instruction_title_h + 5), instruction_new, font=regular_font,
                  fill="black")

    buffer = BytesIO()
    out_img.convert("RGB").save(fp=buffer, format='PNG')
    buff_val = buffer.getvalue()
    return ContentFile(buff_val, file_name)


def draw_meta_item(out_img, key, value, icon_file, x_offset, y_offset, draw):
    meta_icon_img = Image.open(icon_file)
    icon_w, icon_h = meta_icon_img.size
    offset = (x_offset, y_offset)

    out_img.paste(meta_icon_img, offset, meta_icon_img)

    roboto_regular_font_path = fonts.get("Roboto-Regular")
    roboto_bold_font_path = fonts.get("Roboto-Bold")

    meta_font_size = 16
    regular_font = ImageFont.truetype(roboto_regular_font_path, meta_font_size)
    bold_font = ImageFont.truetype(roboto_bold_font_path, meta_font_size)

    padding = 10

    label_x_offset = x_offset + icon_w + padding
    label_y_offset = y_offset + 7

    label = f"{key}: "
    _, _, label_w, label_h = draw.textbbox((0, 0), label, font=regular_font)
    draw.text((label_x_offset, label_y_offset), text=label, font=regular_font, fill="black")

    _, _, value_w, value_h = draw.textbbox((0, 0), value, font=bold_font)
    draw.text((label_x_offset + label_w + 5, label_y_offset), text=value, font=bold_font, fill="black")

    return icon_h
