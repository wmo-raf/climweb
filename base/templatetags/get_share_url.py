from django import template
from django.conf import settings

register = template.Library()

SOCIAL_MEDIA_SHARE_CONFIG = getattr(settings, 'SOCIAL_MEDIA_SHARE_CONFIG', {})


@register.simple_tag
def get_social_media_share(platform, url, text=None):
    share_url = None

    try:
        config = SOCIAL_MEDIA_SHARE_CONFIG[platform]

        base_config = config.get('base_url', None)
        url_config = config.get('link_param', None)
        text_config = config.get('text_param', None)

        if base_config and url_config:
            text_param = None
            url_param = None

            if url_config and url:
                url_param = '{}={}'.format(url_config, url)

            if text_config and text:
                text_param = '{}={}'.format(text_config, text)

            if url_param:
                share_url = '{}?{}'.format(base_config, url_param)
                if text_param:
                    share_url = '{}&{}'.format(share_url, text_param)

            return share_url
    except KeyError:
        return None

    return share_url