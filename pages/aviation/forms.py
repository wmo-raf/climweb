from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from pages.aviation.models import Message

class AirportLoaderForm(forms.Form):
    file = forms.FileField(label="File", required=True)
    overwrite_existing = forms.BooleanField(label="Overwrite existing data", required=False)
    data = forms.JSONField(widget=forms.HiddenInput)

    # only allow csv files
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs.update({'accept': '.csv'})

    def clean(self):
        cleaned_data = super().clean()
        data = cleaned_data.get("data")
        fields = data.get("fields")
        rows = data.get("rows")

        if not fields or not rows:
            self.add_error(None, "No data found in the table.")
            return cleaned_data

        fields = data.get("fields")
        rows = data.get("rows")

        airports = []
        added_airports = []
        for row in rows:
            data_dict = dict(zip(fields, row))
            id = data_dict.get("ID")
            airport = data_dict.get("Airport")
            lat = data_dict.get("Latitude")
            lon = data_dict.get("Longitude")
            category = data_dict.get("Category")

            if airport in added_airports:
                self.add_error(None,
                               f"Duplicate airport found in table data: '{airport}'. "
                               f"Please remove the duplicate entry and try again.")
                return cleaned_data

            added_airports.append(airport)
            airports.append({"id":id, "airport": airport, "lat": lat, "lon": lon, "category": category})

        cleaned_data["data"] = airports

        return cleaned_data


class MessageForm(forms.ModelForm):
    
    class Meta:
        model = Message
        fields = ['msg_encode', ]