from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from estuairefleet.alerts.models import AlertStatus, DriverResponseType
from estuairefleet.alerts.services import escalate_alert, evaluate_route_alert, respond_to_alert
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
    make_student(1, route)

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
    assert alert.__class__.objects.get(pk=alert.pk).status == AlertStatus.IN_PROGRESS
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
