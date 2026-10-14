from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from estuairefleet.core import conf
from estuairefleet.core.exceptions import InvalidBusTransition
from estuairefleet.core.geo import haversine_m, is_valid_lat_lng

from .models import Bus, BusStatus, Campus, Incident, IncidentStatus, Stop, Trajet

STATUS_TRANSITIONS = {
    BusStatus.HORS_SERVICE: {BusStatus.DISPONIBLE},
    BusStatus.DISPONIBLE: {BusStatus.EN_ROUTE, BusStatus.INDISPONIBLE, BusStatus.HORS_SERVICE},
    BusStatus.EN_ROUTE: {BusStatus.DISPONIBLE, BusStatus.PLEIN, BusStatus.INDISPONIBLE},
    BusStatus.PLEIN: {BusStatus.DISPONIBLE},
    BusStatus.INDISPONIBLE: {BusStatus.DISPONIBLE, BusStatus.HORS_SERVICE},
}


def _is_admin(user):
    return user and (user.is_superuser or user.role in {"admin", "administrator"})


@transaction.atomic
def create_campus(**data):
    return Campus.objects.create(**data)


@transaction.atomic
def update_campus(*, campus, **data):
    for key, value in data.items():
        setattr(campus, key, value)
    campus.full_clean()
    campus.save()
    return campus


@transaction.atomic
def deactivate_campus(*, campus):
    campus.is_active = False
    campus.save(update_fields=["is_active", "updated_at"])
    return campus


@transaction.atomic
def create_trajet(*, stops=None, **data):
    trajet = Trajet.objects.create(**data)
    for item in stops or []:
        Stop.objects.create(trajet=trajet, **item)
    return trajet


@transaction.atomic
def update_trajet(*, trajet, stops=None, **data):
    for key, value in data.items():
        setattr(trajet, key, value)
    trajet.full_clean()
    trajet.save()
    if stops is not None:
        trajet.stops.all().delete()
        Stop.objects.bulk_create([Stop(trajet=trajet, **item) for item in stops])
    return trajet


@transaction.atomic
def create_bus(**data):
    bus = Bus(**data)
    bus.full_clean()
    bus.save()
    return bus


@transaction.atomic
def update_bus(*, bus, **data):
    for key, value in data.items():
        setattr(bus, key, value)
    bus.full_clean()
    bus.save()
    return bus


@transaction.atomic
def assign_chauffeur(*, bus, chauffeur):
    if chauffeur and Bus.objects.filter(chauffeur=chauffeur).exclude(pk=bus.pk).exists():
        raise ValueError("Ce chauffeur a déjà un bus affecté.")
    bus.chauffeur = chauffeur
    bus.save(update_fields=["chauffeur", "updated_at"])
    return bus


assign_driver = assign_chauffeur


@transaction.atomic
def assign_trajet(*, bus, trajet):
    bus.trajet = trajet
    bus.save(update_fields=["trajet", "updated_at"])
    return bus


@transaction.atomic
def change_bus_status(*, bus, new_status, by):
    locked = Bus.objects.select_for_update().get(pk=bus.pk)
    if not _is_admin(by) and (not by or not getattr(by, "chauffeur", None) or locked.chauffeur_id != by.chauffeur.pk):
        raise PermissionDenied("Seul le chauffeur du bus ou un administrateur peut modifier ce statut.")
    allowed = _is_admin(by) and new_status == BusStatus.HORS_SERVICE
    allowed = allowed or new_status in STATUS_TRANSITIONS.get(locked.status, set())
    if not allowed:
        raise InvalidBusTransition(
            f"Le bus ne peut pas passer de « {locked.get_status_display()} » à « {new_status} ».",
        )
    locked.status = new_status
    locked.status_changed_at = timezone.now()
    locked.save(update_fields=["status", "status_changed_at", "updated_at"])
    return locked


@transaction.atomic
def update_bus_position(*, bus, lat, lng, by):
    locked = Bus.objects.select_for_update().get(pk=bus.pk)
    if not _is_admin(by) and (not by or not getattr(by, "chauffeur", None) or locked.chauffeur_id != by.chauffeur.pk):
        raise PermissionDenied("Seul le chauffeur du bus peut partager sa position.")
    if not is_valid_lat_lng(lat, lng):
        raise ValidationError("La position du bus est invalide.")
    now = timezone.now()
    if locked.position_updated_at and (now - locked.position_updated_at).total_seconds() < 3:
        return locked
    locked.position_lat, locked.position_lng, locked.position_updated_at = lat, lng, now
    locked.save(update_fields=["position_lat", "position_lng", "position_updated_at", "updated_at"])
    return locked


@transaction.atomic
def set_bus_occupancy(*, bus, places, by):
    locked = Bus.objects.select_for_update().get(pk=bus.pk)
    if not _is_admin(by) and (not by or not getattr(by, "chauffeur", None) or locked.chauffeur_id != by.chauffeur.pk):
        raise PermissionDenied("Seul le chauffeur du bus peut modifier les places occupées.")
    if places < 0 or places > locked.capacity:
        raise ValueError("Le nombre de places doit rester compris entre zéro et la capacité.")
    previous_status = locked.status
    locked.places_occupees = places
    if places == locked.capacity and locked.status == BusStatus.EN_ROUTE:
        locked.status = BusStatus.PLEIN
    elif places < locked.capacity and locked.status == BusStatus.PLEIN:
        locked.status = BusStatus.DISPONIBLE
    if locked.status != previous_status:
        locked.status_changed_at = timezone.now()
    locked.save(update_fields=["places_occupees", "status", "status_changed_at", "updated_at"])
    return locked


@transaction.atomic
def report_incident(*, incident=None, by=None, **data):
    if incident is None:
        incident = Incident(**data, reported_by=by)
        incident.full_clean()
        incident.save()
        return incident
    locked = Incident.objects.select_for_update().get(pk=incident.pk)
    for key, value in data.items():
        setattr(locked, key, value)
    locked.full_clean()
    locked.save()
    return locked


@transaction.atomic
def resolve_incident(*, incident, by=None):
    locked = Incident.objects.select_for_update().get(pk=incident.pk)
    if locked.status != IncidentStatus.RESOLU:
        locked.resolve(by=by)
    return locked


def estimate_eta(*, bus, point):
    if bus.position_lat is None or bus.position_lng is None:
        return None
    seconds = haversine_m((bus.position_lat, bus.position_lng), point) / (conf.AVG_BUS_SPEED_KMH * 1000 / 3600)
    return timezone.now() + timedelta(seconds=seconds)
