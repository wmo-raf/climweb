from site_settings.models import Theme


def theme(request):

    theme_ls = Theme.objects.get(is_default = True)

    if theme_ls:
        theme = {
            'primary_color': theme_ls.primary_color,
            'secondary_color': theme_ls.secondary_color,
            'border_radius': f"{theme_ls.border_radius * 0.06}em",
            'box_shadow': f"elevation-{theme_ls.box_shadow}",
        }
    else:
        theme = {

        }

    return theme