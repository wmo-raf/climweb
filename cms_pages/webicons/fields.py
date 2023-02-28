import os
import xml.etree.cElementTree as et

from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import FileField
from django.template.defaultfilters import filesizeformat

ALLOWED_EXTENSIONS = ['svg']
SUPPORTED_FORMATS_TEXT = ("SVG")


class SVGField(FileField):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Get max upload size from settings
        self.max_upload_size = getattr(settings, 'WAGTAILIMAGES_MAX_UPLOAD_SIZE', 10 * 1024 * 1024)

        max_upload_size_text = filesizeformat(self.max_upload_size)

        # Help text
        if self.max_upload_size is not None:
            self.help_text = (
                "Supported formats: %(supported_formats)s. Maximum filesize: %(max_upload_size)s."
            ) % {
                                 'supported_formats': SUPPORTED_FORMATS_TEXT,
                                 'max_upload_size': max_upload_size_text,
                             }
        else:
            self.help_text = (
                "Supported formats: %(supported_formats)s."
            ) % {
                                 'supported_formats': SUPPORTED_FORMATS_TEXT,
                             }

        # Error messages
        self.error_messages['invalid_image'] = (
            "Not a supported format. Supported formats: %s."
        ) % SUPPORTED_FORMATS_TEXT

        self.error_messages['invalid_image_known_format'] = (
            "Not a valid SVG image."
        )

        self.error_messages['file_too_large'] = (
            "This file is too big (%%s). Maximum filesize %s."
        ) % max_upload_size_text

        self.error_messages['file_too_large_unknown_size'] = (
            "This file is too big. Maximum filesize %s."
        ) % max_upload_size_text

    def check_image_file_size(self, f):
        # Upload size checking can be disabled by setting max upload size to None
        if self.max_upload_size is None:
            return

        # Check the filesize
        if f.size > self.max_upload_size:
            raise ValidationError(self.error_messages['file_too_large'] % (
                filesizeformat(f.size),
            ), code='file_too_large')

    def check_image_file_format(self, f):
        # Check file extension
        extension = os.path.splitext(f.name)[1].lower()[1:]

        if extension not in ALLOWED_EXTENSIONS:
            raise ValidationError(self.error_messages['invalid_image'], code='invalid_image')

    def check_if_svg(self, f):
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
            raise ValidationError(self.error_messages['invalid_image_known_format'], code='invalid_image_known_format')

        # Do not forget to "reset" file
        f.seek(0)

    def to_python(self, data):
        f = super().to_python(data)

        print(f)

        if f is not None:
            self.check_image_file_size(f)
            self.check_image_file_format(f)
            self.check_if_svg(f)

        return f
