from django import forms
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

from .models import ShortLink


class PublicShortLinkForm(forms.ModelForm):
    """
    Form used on the public, unauthenticated "shorten a link" page. Only
    exposes the target URL - everything else (short code generation,
    source, created_by) is handled server-side.
    """

    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox, label="")

    class Meta:
        model = ShortLink
        fields = ["target_url"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target_url"].label = _("URL to shorten")
        # Restrict to http/https so people can't submit javascript:/data: etc.
        self.fields["target_url"].validators.append(URLValidator(schemes=["http", "https"]))
        self.fields["target_url"].widget.attrs.setdefault(
            "placeholder", "https://example.com/a-very-long-url-goes-here"
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.source = ShortLink.Source.PUBLIC
        if commit:
            instance.save()
        return instance
