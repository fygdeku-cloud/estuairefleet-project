from django import forms

from estuairefleet.fleet.models import Trajet


class SignalForm(forms.Form):
    trajet = forms.ModelChoiceField(queryset=Trajet.objects.filter(is_active=True), label="Trajet", required=False)
    position_lat = forms.DecimalField(max_digits=9, decimal_places=6)
    position_lng = forms.DecimalField(max_digits=9, decimal_places=6)
