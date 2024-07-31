from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from pages.aviation.models import Message

class StationLoaderForm(forms.Form):
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

        stations = []
        added_stations = []
        for row in rows:
            data_dict = dict(zip(fields, row))
            station = data_dict.get("Station")
            lat = data_dict.get("Latitude")
            lon = data_dict.get("Longitude")
            category = data_dict.get("Category")

            if station in added_stations:
                self.add_error(None,
                               f"Duplicate station found in table data: '{station}'. "
                               f"Please remove the duplicate entry and try again.")
                return cleaned_data

            added_stations.append(station)
            stations.append({"station": station, "lat": lat, "lon": lon, "category": category})

        cleaned_data["data"] = stations

        return cleaned_data


class MessageForm(forms.ModelForm):
    
    class Meta:
        model = Message
        fields = ['msg_encode', ]