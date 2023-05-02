import xml.etree.cElementTree as et
import datetime

import pytz
from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


def validate_svg(f):
    # Find "start" word in file and get "tag" from there
    f.seek(0)
    tag = None
    try:
        for event, el in et.iterparse(f, ('start',)):
            tag = el.tag
            break
    except et.ParseError:
        pass

    # Check that this "tag" is correct
    if tag != '{http://www.w3.org/2000/svg}svg':
        raise ValidationError('Uploaded file is not an image or SVG file.')

    # Do not forget to "reset" file
    f.seek(0)

    return f


def get_years(start_year=2019, as_choices=False):
    years = []
    for r in range(start_year, (datetime.datetime.now().year + 1)):
        if as_choices:
            years.append((r, r))
        else:
            years.append(r)
    return years


def paginate(queryset, current_page, per_page=6):
    # Paginate all items by per_page
    paginator = Paginator(queryset, per_page)
    # Try to get the ?page=x value
    try:
        # If the page exists and the ?page=x is an int
        items = paginator.page(current_page)
    except PageNotAnInteger:
        # If the ?page=x is not an int; show the first page
        items = paginator.page(1)
    except EmptyPage:
        # If the ?page=x is out of range (too high most likely)
        # Then return the last page
        items = paginator.page(paginator.num_pages)
    return items


def query_param_to_list(query_param, as_int=False):
    if query_param:
        # convert to list and remove empty items
        query_param_list = filter(None, query_param.split(','))

        if as_int:
            # convert to int
            query_param_list = map(int, query_param_list)

        try:
            return list(query_param_list)
        except ValueError:
            # TODO: Return error message
            pass

    return None


def get_first_img_src(html):
    # parse html and get first image src
    soup = BeautifulSoup(html, 'html.parser')
    img = soup.find('img')
    if img and img['src']:
        return img['src']
    return None


def get_first_non_empty_p_string(html):
    # parse html and get first non empty p tag text
    soup = BeautifulSoup(html, 'html.parser')

    p = soup.find(lambda tag: tag.name == 'p' and tag.text is not None and tag.text.strip() != "")
    if p:
        return p.text
    return None


def get_object_or_none(model_class, **kwargs):
    try:
        return model_class.objects.get(**kwargs)
    except model_class.DoesNotExist:
        return None


def getWeeklyEndDate():
    return datetime.date.today() + datetime.timedelta(days=8)


def getDekadalEndDate():
    return datetime.date.today() + datetime.timedelta(days=10)


def getEndDate():
    return datetime.date.today() + datetime.timedelta(days=10)


def get_pytz_gmt_offset_str(tz):
    gmt_timezone = pytz.timezone('Greenwich')
    time_ref = datetime.datetime(2000, 1, 1)
    time_zero = gmt_timezone.localize(time_ref)

    delta = (time_zero - tz.localize(time_ref)).total_seconds()
    h = (datetime.datetime.min + datetime.timedelta(seconds=delta.__abs__())).hour
    gmt_diff = datetime.time(h).strftime('%H:%M')

    gmt_offset = "GMT{sign}{gmt_diff} {timezone}".format(
        sign="-" if delta < 0 else "+",
        gmt_diff=gmt_diff,
        timezone=tz.zone.replace('_', ' '))

    return gmt_offset

