from django import forms

from .models import AlertResponse


class AlertResponseForm(forms.ModelForm):
    class Meta:
        model = AlertResponse
        fields = ("response_type", "eta_minutes", "reason", "relay_bus")
