import calendar
import os
from datetime import datetime, date
from html.parser import HTMLParser

from django import template
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import stringfilter, truncatewords_html
from django.utils.safestring import mark_safe
from loguru import logger
from wagtail.models import Site, Page

from climweb import __version__
from climweb.base.models import LanguageSettings
from climweb.base.utils import get_first_non_empty_p_string
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def cms_version():
    return __version__


@register.filter
def is_future(self):
    return datetime.today().date() < self.date()


@register.simple_tag
def get_page_by_url(url):
    return get_object_or_404(Page, url=url)


@register.filter(name='range')
def filter_range(start, end):
    return range(start, end)


@register.filter
def subtract(value, arg):
    return value - arg


@register.simple_tag
def setvar(val=None):
    return val


@register.filter
def file_extension(path):
    name, extension = os.path.splitext(path)
    return extension


@register.simple_tag
def get_active_groups(groups, products):
    active_groups = []
    active_resource_type = None
    
    for group in groups:
        for product in products:
            if product.resource_type.group.name == group.name:
                active_groups.append(group)
                if not active_resource_type:
                    active_resource_type = product.resource_type
                break
    
    return {"active_groups": active_groups, "active_resource_type": active_resource_type}


@register.filter
def month_name(month_number):
    return calendar.month_name[month_number]


@register.filter
def django_settings(value):
    return getattr(settings, value, None)


@register.simple_tag(takes_context=True)
def is_active_page(context, curr_page, other_page):
    if hasattr(curr_page, 'get_url') and hasattr(other_page, 'get_url'):
        curr_url = curr_page.get_url(context['request'])
        other_url = other_page.get_url(context['request'])
        return curr_url == other_url
    return False


@stringfilter
def parse_date(date_string, date_format):
    """
    Return a datetime corresponding to date_string, parsed according to format.

    For example, to re-display a date string in another format::

        {{ "01/01/1970"|parse_date:"%m/%d/%Y"|date:"F jS, Y" }}

    """
    try:
        return datetime.strptime(date_string, date_format)
    except ValueError:
        return None


register.filter(parse_date)


@stringfilter
def remove_param(query_string, key):
    """
    Removes a given parameter from a query_string.

    For example, to delete page from "page=1&page=2&year=2020"

        {{ "page=1&page=2&year=2020"|remove_param:"page" }}

        returns year=2020

    """
    
    query_string = query_string.replace("&amp;", "&")
    
    params = query_string.split("&")
    
    url = ""
    
    for param in params:
        if param:
            v = param.split('=')
            if v[0] != key:
                url += param + "&"
    return url


register.filter(remove_param)


@register.filter()
def split(value, key):
    """
        Returns the value turned into a list.
    """
    return value.split(key)


@register.simple_tag
def default_site():
    return Site.objects.filter(is_default_site=True).first()


@register.filter
def get_dict_item(d, k):
    """
    Return the value of a dictionary for a given key. If the key does not exist, return None.
    """
    return d.get(k, None)


class SVGNotFound(Exception):
    pass


@register.simple_tag
def svg(filename, is_static=False):
    MEDIA_ROOT = getattr(settings, 'MEDIA_ROOT')
    
    path = None
    
    if is_static:
        BASE_DIR = getattr(settings, 'BASE_DIR')
        path = os.path.join(BASE_DIR, 'svg', '{filename}'.format(
            filename=filename))
        
        if not path:
            message = "SVG '{filename}' not found".format(filename=filename)
            
            # Raise exception if DEBUG is True, else just log a warning.
            if settings.DEBUG:
                raise SVGNotFound(message)
            else:
                logger.warning(message)
            return ''
    else:
        if MEDIA_ROOT:
            svg_path = os.path.join(MEDIA_ROOT, '{filename}'.format(
                filename=filename))
            
            if os.path.isfile(svg_path):
                path = svg_path
    
    # Sometimes path can be a list/tuple if there's more than one file found
    if isinstance(path, (list, tuple)):
        path = path[0]
    
    if path is not None:
        with open(path) as svg_file:
            svg = mark_safe(svg_file.read())
        
        return svg
    
    return ''


@register.filter
def html_summary(html, words_count=100):
    summary = get_first_non_empty_p_string(html)
    if summary:
        summary = truncatewords_html(summary, words_count)
    return summary


@register.simple_tag
def get_default_site_lang():
    site = Site.objects.filter(is_default_site=True).first()
    lang_settings = LanguageSettings.for_site(site=site)
    default_language = lang_settings.default_language
    return default_language


class ExcludeImagesParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
    
    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'img':
            return
        
        attr_repl = [f"{attr[0]}=\"{attr[1]}\"" for attr in attrs]
        self.result.append(f'<{tag} {" ".join(attr_repl)}>')
    
    def handle_endtag(self, tag):
        if tag.lower() == 'img':
            return
        self.result.append(f'</{tag}>')
    
    def handle_data(self, data):
        self.result.append(data)


def exclude_images(value):
    parser = ExcludeImagesParser()
    parser.feed(value)
    return ''.join(parser.result)


register.filter('exclude_images', exclude_images)


@register.filter
def date_is_today(value):
    """Returns True if the given date is today."""
    return value == date.today()



@register.simple_tag(takes_context=True)
def render_charts(context, charts_block):
    rendered_output = ""
    i = 0
    while i < len(charts_block):
        current = charts_block[i]
        next_chart = charts_block[i + 1] if i + 1 < len(charts_block) else None

        current_desc = getattr(current, "description", None)
        next_desc = getattr(next_chart, "description", None) if next_chart else None

        # If both current and next chart have no description, render them side by side
        if not current_desc and not next_desc and next_chart:
            rendered = render_to_string(
                "partials/chart_pair.html",
                {"charts": [current, next_chart], "index": i + 1},
                request=context["request"]
            )
            rendered_output += rendered
            i += 2
        else:
            rendered = render_to_string(
                "partials/chart_single.html",
                {"chart": current, "index": i + 1},
                request=context["request"]
            )
            rendered_output += rendered
            i += 1
    return mark_safe(rendered_output)