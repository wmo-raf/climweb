from django import forms


class CMSUpgradeForm(forms.Form):
    current_version = forms.CharField(max_length=100, required=True, widget=forms.HiddenInput)
    latest_version = forms.CharField(max_length=100, required=True, widget=forms.HiddenInput)
