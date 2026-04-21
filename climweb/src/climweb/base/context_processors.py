from climweb.base.utils import mix_with_white
from django.core.exceptions import ObjectDoesNotExist

from climweb.base.models import Theme

default_theme = {
    'text_color': '#363636',
    'primary_color': '#0C447C',
    'background_color': '#E6F1FB',
    'border_radius': '12px',
    'box_shadow': 'elevation-1',
}


def theme(request):
    try:
        d_theme = Theme.objects.get(is_default=True)
        return {
            'primary_color': d_theme.primary_hover_color,
            'text_color': d_theme.primary_color,
            'background_color': mix_with_white(d_theme.primary_hover_color, 0.8),
            'border_radius': f"{d_theme.border_radius * 0.06}em",
            'box_shadow': f"elevation-{d_theme.box_shadow}",
        }
    except ObjectDoesNotExist:
        return default_theme
