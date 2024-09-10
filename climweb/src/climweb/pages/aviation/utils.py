from django.templatetags.static import static

from .constants import WIND_BARBS, CLOUD_COVER


def get_wind_barb_icons():
    icons = [
        {
            "value": condition["id"],
            **condition,
            'icon_url': static("img/barbs/{0}.png".format(condition["id"]))} for condition in
        WIND_BARBS
    ]

    return icons


def get_cloud_cover_icons():
    icons = [
        {
            "value": condition["id"],
            **condition,
            'icon_url': static("img/cloud/{0}.png".format(condition["id"]))} for condition in
        CLOUD_COVER
    ]

    return icons
