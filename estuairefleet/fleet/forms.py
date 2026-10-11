from django import forms

from .models import Bus


class BusForm(forms.ModelForm):
    class Meta:
        model = Bus
        fields = ("plate_number", "label", "capacity", "status", "chauffeur", "trajet")
