from django import template

from ..subnational import querystring

register = template.Library()


@register.simple_tag(takes_context=True)
def filter_url(context, **changes):
    """The current query string with the given filter params replaced, or removed when None"""
    return querystring(context.get("request"), **changes)
