from django.db import models
from django.db.models import Count
from django.utils import timezone

from estuairefleet.core.geo import haversine_m

from .models import Bus, Campus, Trajet


def get_active_trajets(now=None):
    now = now or timezone.localtime()
    return [
        trajet
        for trajet in Trajet.objects.filter(is_active=True).prefetch_related("campuses", "stops", "buses")
        if trajet.is_in_service(now)
    ]


def get_trajet_detail(id):
    return Trajet.objects.prefetch_related("campuses", "stops", "buses__chauffeur__user").get(pk=id)


def get_trajets_in_service(now=None):
    return get_active_trajets(now)


def get_buses_for_map(user=None):
    return list(
        Bus.objects.filter(trajet__is_active=True)
        .select_related("trajet", "chauffeur__user")
        .values(
            "id",
            "plate_number",
            "status",
            "position_lat",
            "position_lng",
            "position_updated_at",
            "trajet_id",
            "trajet__name",
            "places_occupees",
            "capacity",
        )
    )


def get_bus_for_chauffeur(user):
    return Bus.objects.select_related("trajet", "chauffeur__user").get(chauffeur__user=user)


def get_buses_for_trajet(trajet):
    return Bus.objects.filter(trajet=trajet).select_related("chauffeur__user")


def get_fleet_overview_counts():
    return {row["status"]: row["count"] for row in Bus.objects.values("status").annotate(count=Count("id"))}


def get_campuses():
    return Campus.objects.filter(is_active=True)


def get_free_chauffeurs():
    from estuairefleet.users.models import Chauffeur

    return Chauffeur.objects.select_related("user").filter(user__is_active=True, bus__isnull=True)


def get_nearest_available_bus(*, latitude, longitude):
    """Retourne le bus de relais le plus proche avec des places disponibles."""
    candidates = Bus.objects.filter(
        status__in=("disponible", "en_route"),
        chauffeur__isnull=False,
        places_occupees__lt=models.F("capacity"),
        position_lat__isnull=False,
        position_lng__isnull=False,
    ).select_related("trajet", "chauffeur__user")
    return min(
        candidates,
        key=lambda bus: haversine_m((latitude, longitude), (bus.position_lat, bus.position_lng)),
        default=None,
    )
