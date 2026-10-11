import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from estuairefleet.core.geo import is_valid_lat_lng


def validate_lat_lng(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2 or not is_valid_lat_lng(value[0], value[1]):
        raise ValidationError(_("Chaque point doit contenir une latitude et une longitude valides."))


def validate_itinerary(value):
    if not isinstance(value, list) or len(value) < 2:
        raise ValidationError(_("L'itinéraire doit contenir au moins deux points."))
    for point in value:
        validate_lat_lng(point)


def validate_horaires(value):
    if not isinstance(value, list):
        raise ValidationError(_("Les horaires doivent être une liste."))
    if any(not isinstance(item, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", item) for item in value):
        raise ValidationError(_("Chaque horaire doit respecter le format HH:MM."))
    if value != sorted(value):
        raise ValidationError(_("Les horaires doivent être dans l'ordre croissant."))


def validate_days_of_week(value):
    if not isinstance(value, list) or any(not isinstance(day, int) or day < 0 or day > 6 for day in value):
        raise ValidationError(_("Les jours doivent être des entiers compris entre 0 et 6."))


validate_route_coordinates = validate_itinerary
