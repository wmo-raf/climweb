import json

from django import forms
from django.template.loader import render_to_string

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets import AdminChooser

from .models import WebIcon


class AdminWebIconChooser(AdminChooser):
    choose_one_text = ('Choose an svg image')
    choose_another_text = ('Change svg image')
    link_to_chosen_text = ('Edit this svg image')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.icon_model = WebIcon

    def render_html(self, name, value, attrs):
        instance, value = self.get_instance_and_id(self.icon_model, value)
        original_field_html = super().render_html(name, value, attrs)

        return render_to_string("webicons/widgets/icon_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'icon': instance,
        })

    def render_js_init(self, id_, name, value):
        return "createIconChooser({0});".format(json.dumps(id_))

    @property
    def media(self):
        return forms.Media(js=[
            versioned_static('webicons/js/icon-chooser-modal.js'),
            versioned_static('webicons/js/icon-chooser.js'),
        ])
