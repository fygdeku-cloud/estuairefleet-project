from django.core.exceptions import ValidationError


def validate_headcount(value):
    if value < 0:
        raise ValidationError("L'effectif doit être positif ou nul.")
