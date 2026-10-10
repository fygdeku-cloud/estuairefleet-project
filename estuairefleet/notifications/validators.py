from django.core.exceptions import ValidationError


def validate_notification_message(value):
    if not value.strip():
        raise ValidationError("Le message ne peut pas être vide.")
