from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from estuairefleet.alerts.models import AlertStatus, DriverResponseType
from estuairefleet.alerts.services import (
    escalate_alert,
    evaluate_route_alert,
    respond_to_alert,
    respond_to_relay,
)
from estuairefleet.fleet.models import Bus, BusStatus, Trajet
from estuairefleet.signals.services import emit_signal
from estuairefleet.users.models import Chauffeur, Student, User


def make_student(index, route):
    user = User.objects.create_user(email=f"student-{index}@example.test", password="password", role="student")
    student = Student.objects.create(user=user, consent_location=True)
    student.trajets_habituels.add(route)
    emit_signal(student=user, trajet=route, lat=3.8667, lng=11.5167)
    return student


@pytest.mark.django_db
def test_alert_notifies_assigned_driver_and_accepts_response():
    route = Trajet.objects.create(name="Route alerte", itinerary=[[3.8667, 11.5167], [3.87, 11.52]], seuil_alerte=1)
    driver = User.objects.create_user(email="driver@example.test", password="password", role="driver")
    chauffeur = Chauffeur.objects.create(user=driver, licence_number="LIC-ALERT")
    bus = Bus.objects.create(
        plate_number="CE-ALERT", capacity=20, status=BusStatus.DISPONIBLE, chauffeur=chauffeur, trajet=route
    )
    student = make_student(1, route)

    alert = evaluate_route_alert(route=route)

    assert alert.priority is True
    assert driver.notifications.filter(title="Nouvelle alerte sur votre trajet").exists()
    response = respond_to_alert(
        alert=alert,
        driver=driver,
        response_type=DriverResponseType.ARRIVING,
        eta_minutes=8,
    )
    assert response.driver_id == driver.pk
    assert alert.__class__.objects.get(pk=alert.pk).status == AlertStatus.RESOLVED
    student.refresh_from_db()
    signal = student.signals.get()
    assert signal.status == "pris_en_charge"
    assert signal.taken_by_bus_id == bus.pk
    assert bus.pk is not None


@pytest.mark.django_db
def test_alert_response_is_restricted_to_route_driver():
    route = Trajet.objects.create(name="Route privée", itinerary=[[3.8667, 11.5167], [3.87, 11.52]], seuil_alerte=1)
    other_route = Trajet.objects.create(name="Autre route", itinerary=[[3.9, 11.55], [3.91, 11.56]], seuil_alerte=1)
    driver = User.objects.create_user(email="driver2@example.test", password="password", role="driver")
    Chauffeur.objects.create(user=driver, licence_number="LIC-OTHER")
    Bus.objects.create(
        plate_number="CE-OTHER",
        capacity=20,
        status=BusStatus.DISPONIBLE,
        chauffeur=driver.chauffeur,
        trajet=other_route,
    )
    make_student(2, route)
    alert = evaluate_route_alert(route=route)

    with pytest.raises(PermissionDenied):
        respond_to_alert(alert=alert, driver=driver, response_type=DriverResponseType.ARRIVING, eta_minutes=5)


@pytest.mark.django_db
def test_expired_response_deadline_escalates():
    route = Trajet.objects.create(name="Route escalade", itinerary=[[3.8667, 11.5167], [3.87, 11.52]], seuil_alerte=1)
    make_student(3, route)
    alert = evaluate_route_alert(route=route)
    alert.response_deadline = timezone.now() - timedelta(minutes=1)
    alert.save(update_fields=["response_deadline", "updated_at"])

    escalated = escalate_alert(alert=alert)

    assert escalated.status == AlertStatus.ESCALATED
    assert escalated.escalated_at is not None


@pytest.mark.django_db
def test_relay_is_accepted_or_passes_to_the_next_bus():
    route = Trajet.objects.create(name="Route relais", itinerary=[[3.8667, 11.5167]], seuil_alerte=1)
    route_user = User.objects.create_user(email="route-driver@example.test", password="password", role="driver")
    route_driver = Chauffeur.objects.create(user=route_user, licence_number="LIC-ROUTE")
    Bus.objects.create(
        plate_number="CE-ROUTE",
        capacity=20,
        status=BusStatus.EN_ROUTE,
        chauffeur=route_driver,
        trajet=route,
        position_lat=3.8667,
        position_lng=11.5167,
    )
    relay_users = []
    relay_buses = []
    for index, longitude in enumerate((11.5170, 11.5175), start=1):
        user = User.objects.create_user(email=f"relay-{index}@example.test", password="password", role="driver")
        chauffeur = Chauffeur.objects.create(user=user, licence_number=f"LIC-RELAY-{index}")
        relay_buses.append(
            Bus.objects.create(
                plate_number=f"CE-RELAY-{index}",
                capacity=20,
                status=BusStatus.DISPONIBLE,
                chauffeur=chauffeur,
                position_lat=3.8667,
                position_lng=longitude,
            )
        )
        relay_users.append(user)
    student = make_student(20, route)
    alert = evaluate_route_alert(route=route)

    respond_to_alert(
        alert=alert,
        driver=route_user,
        response_type=DriverResponseType.UNAVAILABLE,
        reason="Panne",
        relay_bus=relay_buses[0],
    )
    assert respond_to_relay(alert=alert, driver=relay_users[0], accepted=False).relay_bus_id == relay_buses[1].pk
    resolved = respond_to_relay(alert=alert, driver=relay_users[1], accepted=True)

    assert resolved.status == AlertStatus.RESOLVED
    assert student.signals.filter(status="pris_en_charge").exists()
