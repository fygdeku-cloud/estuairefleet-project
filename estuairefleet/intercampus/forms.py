from django import forms

from .models import CoursInterCampus


class CoursInterCampusForm(forms.ModelForm):
    class Meta:
        model = CoursInterCampus
        fields = (
            "group",
            "campus_depart",
            "campus_arrivee",
            "start_at",
            "horaire_fin",
            "effectif",
            "bus_affecte",
            "notify_before_minutes",
            "status",
        )
        widgets = {
            "start_at": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "ef-input"}),
            "horaire_fin": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "ef-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "ef-input")
