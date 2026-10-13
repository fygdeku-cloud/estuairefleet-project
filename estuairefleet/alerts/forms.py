from django import forms

from .models import AlertResponse


class AlertResponseForm(forms.ModelForm):
    class Meta:
        model = AlertResponse
        fields = ("response_type", "eta_minutes", "reason", "relay_bus")
        labels = {
            "response_type": "Réponse",
            "eta_minutes": "Délai estimé (minutes)",
            "reason": "Motif",
            "relay_bus": "Bus relais proposé",
        }
