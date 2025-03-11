import urllib.parse

from django import template
from django.conf import settings

register = template.Library()

ONLINE_SHARE_CONFIG = getattr(settings, 'ONLINE_SHARE_CONFIG', {})


@register.inclusion_tag("social_media_share_buttons_include.html")
def share_buttons(url, text=None):
    share_urls = []
    for config in ONLINE_SHARE_CONFIG:
        enabled = config.get('enabled', False)
        name = config.get('name', None)
        base_url = config.get('base_url', None)
        link_param = config.get('link_param', None)
        text_in_url = config.get('text_in_url', False)
        text_param = config.get('text_param', None)
        encode = config.get('encode', False)
        fa_icon = config.get('fa_icon', False)
        svg_icon = config.get('svg_icon', None)
        
        link_query = None
        text_query = None
        
        item_url = url
        item_text = text
        
        if not enabled or not name or not base_url or not link_param:
            continue
        
        if encode:
            item_url = urllib.parse.quote(item_url)
            if item_text:
                item_text = urllib.parse.quote(item_text)
        
        if item_text:
            if text_in_url:
                item_url = f"{item_text}%20{item_url}"
            elif text_param:
                text_query = f"{text_param}={item_text}"
        
        if link_param and item_url:
            link_query = f"{link_param}={item_url}"
        
        share_url = f"{base_url}?{link_query}"
        
        if text_query:
            share_url = f"{share_url}&{text_query}"
        
        share_urls.append({
            'name': name,
            'url': share_url,
            'fa_icon': fa_icon,
            "svg_icon": svg_icon
        })
    
    return {"share_urls": share_urls}
