from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_route_coordinates(value):
    if not isinstance(value, list):
        raise ValidationError(_("L'itinéraire doit être une liste de coordonnées."))
