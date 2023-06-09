from site_settings.models import Theme


def theme(request):

    theme_ls = Theme.objects.all()
    
    for theme_item in theme_ls:
        if theme_item.is_default:
            theme = {
                'primary_color': theme_item.primary_color,
                'primary_hover_color': theme_item.primary_hover_color,
                'secondary_color': theme_item.secondary_color,
                'border_radius': f"{theme_item.border_radius * 0.06}em",
                'box_shadow': f"elevation-{theme_item.box_shadow}",
            }
    
        else:
            theme = {
                'primary_color': '#363636', 
                'primary_hover_color': '#67a9ce', 
                'secondary_color': '#ffffff', 
                'border_radius': '1.5em', 
                'box_shadow': 'elevation-1'
            }
    
    
    return theme
