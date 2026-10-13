from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from estuairefleet.core.geo import distance_point_to_polyline_m, haversine_m


def validate_signal_position(*, route, latitude, longitude):
    """Require a signal to be within the configured route geofence."""
    point = (float(latitude), float(longitude))
    distances = [distance_point_to_polyline_m(point, route.polyline)]
    distances.extend(haversine_m(point, stop.point) for stop in route.stops.all())
    distances.extend(haversine_m(point, campus.point) for campus in route.campuses.all())
    if min(distances, default=float("inf")) > route.geofence_radius_m:
        raise ValidationError(_("Le point indiqué est trop éloigné du trajet sélectionné."))
