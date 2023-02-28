from django import forms


class ZoomBatchRegistrationForm(forms.Form):
    zoom_reg_page = forms.IntegerField()