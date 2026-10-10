from math import hypot

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

MAX_ROUTE_DISTANCE_DEGREES = 0.5
COORDINATE_PAIR_LENGTH = 2


def validate_signal_position(*, route, latitude, longitude):
    """Require a signal to be close to a route stop or route campus."""
    points = list(route.itinerary or [])
    points.extend([campus.latitude, campus.longitude] for campus in route.campuses.all())
    if not points:
        return
    if not any(
        hypot(float(latitude) - float(point[0]), float(longitude) - float(point[1])) <= MAX_ROUTE_DISTANCE_DEGREES
        for point in points
        if len(point) >= COORDINATE_PAIR_LENGTH
    ):
        raise ValidationError(_("Le point indiqué est trop éloigné du trajet sélectionné."))
