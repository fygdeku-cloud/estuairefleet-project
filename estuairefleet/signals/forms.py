from django import forms

from .models import Signal


class SignalForm(forms.ModelForm):
    class Meta:
        model = Signal
        fields = ("route", "position_lat", "position_lng")
