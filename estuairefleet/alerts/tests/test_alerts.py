from datetime import timedelta

import pytest
from django.utils import timezone

from estuairefleet.alerts.models import AlertResponse, AlertStatus, DriverResponseType
from estuairefleet.alerts.services import (
    escalate_alert,
    evaluate_route_alert,
    resolve_alert,
    respond_to_alert,
    respond_to_relay,
)
from estuairefleet.signals.models import Signal, SignalStatus


@pytest.mark.django_db
def test_alert_is_triggered_at_five_active_signals(trajet, student, student_factory, bus):
    now = timezone.now()
    students = [student, *(student_factory() for _ in range(4))]
    for profile in students:
        Signal.objects.create(
            student=profile,
            trajet=trajet,
            position_lat="3.8667",
            position_lng="11.5167",
            status=SignalStatus.ACTIF,
            expires_at=now + timedelta(minutes=20),
        )

    alert = evaluate_route_alert(route=trajet)

    assert alert is not None
    assert alert.status == AlertStatus.TRIGGERED
    assert alert.priority
    assert alert.signal_count == 5
    assert alert.signals.count() == 5
    assert bus.chauffeur.user.notifications.filter(notification_type="alert").exists()


@pytest.mark.django_db
def test_driver_arriving_resolves_alert_and_takes_signals(alert, signal, driver, bus):
    alert.signals.add(signal)

    response = respond_to_alert(
        alert=alert,
        driver=driver.user,
        response_type=DriverResponseType.ARRIVING,
        eta_minutes=8,
    )
    alert.refresh_from_db()
    signal.refresh_from_db()

    assert isinstance(response, AlertResponse)
    assert alert.status == AlertStatus.RESOLVED
    assert response.response_type == DriverResponseType.ARRIVING
    assert signal.status == SignalStatus.PRIS_EN_CHARGE
    assert signal.taken_by_bus == bus


@pytest.mark.django_db
def test_driver_unavailable_opens_relay(alert, signal, driver, driver_factory, bus_factory):
    bus_factory(chauffeur=driver, plate_number="CE-ROUTE-EF")
    relay_driver = driver_factory()
    relay_bus = bus_factory(chauffeur=relay_driver, trajet=None, plate_number="CE-RELAY-EF")
    alert.signals.add(signal)

    respond_to_alert(
        alert=alert,
        driver=driver.user,
        response_type=DriverResponseType.UNAVAILABLE,
        reason="Panne mécanique",
        relay_bus=relay_bus,
    )
    alert.refresh_from_db()
    assert alert.status == AlertStatus.RELAY
    assert alert.relay_bus == relay_bus
    assert alert.relay_attempts.filter(bus=relay_bus).exists()


@pytest.mark.django_db
def test_relay_driver_can_accept_relay_request(alert, signal, driver, driver_factory, bus_factory):
    bus_factory(chauffeur=driver, plate_number="CE-ROUTE-EF")
    relay_driver = driver_factory()
    relay_bus = bus_factory(chauffeur=relay_driver, trajet=None, plate_number="CE-RELAY-EF")
    alert.signals.add(signal)

    respond_to_alert(
        alert=alert,
        driver=driver.user,
        response_type=DriverResponseType.UNAVAILABLE,
        reason="Panne mécanique",
        relay_bus=relay_bus,
    )
    resolved = respond_to_relay(alert=alert, driver=relay_driver.user, accepted=True)

    assert resolved.status == AlertStatus.RESOLVED
    assert resolved.relay_attempts.get(bus=relay_bus).accepted is True


@pytest.mark.django_db
def test_expired_alert_is_escalated(alert):
    alert.response_deadline = timezone.now() - timedelta(minutes=1)
    alert.save(update_fields=["response_deadline", "updated_at"])

    escalated = escalate_alert(alert=alert)

    assert escalated.status == AlertStatus.ESCALATED
    assert escalated.escalated_at is not None


@pytest.mark.django_db
def test_timed_out_relay_selects_an_available_relay_bus(alert, signal, driver_factory, bus_factory):
    relay_driver = driver_factory()
    relay_bus = bus_factory(
        chauffeur=relay_driver,
        trajet=None,
        plate_number="CE-RELAY-AUTO-EF",
        position_lat="3.8670",
        position_lng="11.5170",
    )
    alert.status = AlertStatus.RELAY
    alert.response_deadline = timezone.now() - timedelta(minutes=1)
    alert.save(update_fields=["status", "response_deadline", "updated_at"])
    alert.signals.add(signal)

    escalated = escalate_alert(alert=alert)
    escalated.refresh_from_db()

    assert escalated.status == AlertStatus.RELAY
    assert escalated.relay_bus == relay_bus
    assert escalated.relay_attempts.filter(bus=relay_bus).exists()


@pytest.mark.django_db
def test_admin_can_resolve_alert_and_close_its_active_signals(alert, signal, admin_user):
    alert.signals.add(signal)

    resolved = resolve_alert(alert=alert, by=admin_user)
    signal.refresh_from_db()

    assert resolved.status == AlertStatus.RESOLVED
    assert signal.status == SignalStatus.PRIS_EN_CHARGE
    assert signal.closed_by == admin_user
