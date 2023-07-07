from wagtailcache.cache import clear_cache
from wagtail import hooks


@hooks.register('after_create_page')
@hooks.register('after_edit_page')
def clear_wagtailcache(request, page):
    print("....clearing cache on publish...")
    if page.live:
        clear_cache()