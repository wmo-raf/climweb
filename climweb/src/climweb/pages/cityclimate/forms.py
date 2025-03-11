from django import forms
from django.utils.translation import gettext_lazy as _

from .models import City


class ClimateDataForm(forms.Form):
    DATE_FORMAT_CHOICES = (
        ("yyyy-mm-dd", "yyyy-mm-dd"),
        ("dd-mm-yyyy", "dd-mm-yyyy"),
        ("yyyy/mm/dd", "yyyy/mm/dd"),
        ("dd/mm/yyyy", "dd/mm/yyyy")
    )
    
    city = forms.ModelChoiceField(queryset=City.objects.all(), label=_("City"))
    file = forms.FileField(label=_("CSV File"))
    data = forms.JSONField(required=True, widget=forms.HiddenInput)
    date_format = forms.ChoiceField(choices=DATE_FORMAT_CHOICES, label=_("File Date Format"))
    
    def __init__(self, *args, **kwargs):
        city = kwargs.get("city")
        if city:
            kwargs.pop("city")
        
        super().__init__(*args, **kwargs)
        
        if city:
            self.fields['city'].widget.attrs['class'] = "non-interactive"
