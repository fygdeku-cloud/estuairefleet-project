from math import hypot

from django.db.models import QuerySet

from .models import Bus, Campus, Trajet


def get_active_routes() -> QuerySet[Trajet]:
    return Trajet.objects.active().prefetch_related("campuses", "buses")


def get_available_buses() -> QuerySet[Bus]:
    return Bus.objects.filter(status__in=("available", "en_route")).select_related("driver")


def get_nearest_available_bus(*, latitude, longitude) -> Bus | None:
    buses = get_available_buses().filter(position_lat__isnull=False, position_lng__isnull=False)
    return min(
        buses,
        key=lambda bus: hypot(float(bus.position_lat) - float(latitude), float(bus.position_lng) - float(longitude)),
        default=None,
    )


def get_active_campuses() -> QuerySet[Campus]:
    return Campus.objects.active()
