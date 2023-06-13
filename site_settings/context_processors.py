from django.core.exceptions import ObjectDoesNotExist

from site_settings.models import Theme

default_theme = {
    'primary_color': '#363636',
    'primary_hover_color': '#67a9ce',
    'secondary_color': '#ffffff',
    'border_radius': '1.5em',
    'box_shadow': 'elevation-1'
}


def theme(request):
    try:
        theme = Theme.objects.get(is_default=True)
        return {
            'primary_color': theme.primary_color,
            'primary_hover_color': theme.primary_hover_color,
            'secondary_color': theme.secondary_color,
            'border_radius': f"{theme.border_radius * 0.06}em",
            'box_shadow': f"elevation-{theme.box_shadow}",
        }
    except ObjectDoesNotExist:
        return default_theme
