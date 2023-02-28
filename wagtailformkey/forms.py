from captcha.fields import ReCaptchaField
from django import forms
from wagtail.contrib.forms.forms import FormBuilder


class KeyField(forms.CharField):
    widget = forms.HiddenInput()

    def __init__(self, *args, **kwargs):
        super(KeyField, self).__init__(*args, **kwargs)

        self.required = True


class WagtailCaptchaKeyFormBuilder(FormBuilder):
    CAPTCHA_FIELD_NAME = 'wagtailcaptcha'
    KEY_FIELD_NAME = 'wagtailkey'

    @property
    def formfields(self):
        # Add wagtailcaptcha to formfields property
        fields = super(WagtailCaptchaKeyFormBuilder, self).formfields
        fields[self.CAPTCHA_FIELD_NAME] = ReCaptchaField(label='')
        fields[self.KEY_FIELD_NAME] = KeyField(label='')

        return fields


def remove_wagtail_key_field(form):
    form.fields.pop(WagtailCaptchaKeyFormBuilder.KEY_FIELD_NAME, None)
    form.cleaned_data.pop(WagtailCaptchaKeyFormBuilder.KEY_FIELD_NAME, None)