from django.core.exceptions import ObjectDoesNotExist

from climweb.base.models import Theme

default_theme = {
    'primary_color': '#363636',
    'primary_hover_color': '#67a9ce',
    'secondary_color': '#ffffff',
    'border_radius': '0',
    'box_shadow': 'elevation-1',
}


def theme(request):
    try:
        d_theme = Theme.objects.get(is_default=True)
        return {
            'primary_color': d_theme.primary_color,
            'primary_hover_color': d_theme.primary_hover_color,
            'secondary_color': d_theme.secondary_color,
            'border_radius': f"{d_theme.border_radius * 0.06}em",
            'box_shadow': f"elevation-{d_theme.box_shadow}",
        }
    except ObjectDoesNotExist:
        return default_theme
