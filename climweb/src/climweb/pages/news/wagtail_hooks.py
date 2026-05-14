# yourapp/wagtail_hooks.py
from wagtail import hooks
from wagtail.images.formats import Format, register_image_format, unregister_image_format

@hooks.register('register_image_formats')
def custom_image_formats():
    unregister_image_format('fullwidth')
    unregister_image_format('left')
    unregister_image_format('right')

    register_image_format(
        Format('fullwidth', 'Full width',    'richtext-image full-width', 'width-1200')
    )
    register_image_format(
        Format('left',      'Left-aligned',  'richtext-image left',       'width-500')
    )
    register_image_format(
        Format('right',     'Right-aligned', 'richtext-image right',      'width-500')
    )