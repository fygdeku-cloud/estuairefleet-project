from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from estuairefleet.core.exceptions import ActiveSignalExists, ConsentRequired, OutOfZone
from estuairefleet.signals.models import Signal, SignalStatus
from estuairefleet.signals.services import (
    cancel_signal,
    close_signal,
    emit_signal,
    expire_stale_signals,
    flag_false_signal,
)
from estuairefleet.users.services import register_abuse_warning


@pytest.mark.django_db
def test_emit_signal_creates_an_active_signal_and_notification(student, trajet):
    signal = emit_signal(student=student, trajet=trajet, lat="3.8667", lng="11.5167", accuracy=8)

    assert signal.status == SignalStatus.ACTIF
    assert signal.student == student
    assert signal.trajet == trajet
    assert signal.expires_at > timezone.now()
    assert student.user.notifications.filter(notification_type="information").exists()


@pytest.mark.django_db
def test_only_one_active_signal_is_allowed(student, trajet, signal):
    with pytest.raises(ActiveSignalExists):
        emit_signal(student=student, trajet=trajet, lat="3.8667", lng="11.5167")


@pytest.mark.django_db
def test_signal_requires_consent_and_stays_inside_the_route_geofence(student_factory, trajet):
    without_consent = student_factory(consent=False)
    with pytest.raises(ConsentRequired):
        emit_signal(student=without_consent, trajet=trajet, lat="3.8667", lng="11.5167")

    outside = student_factory()
    with pytest.raises(OutOfZone):
        emit_signal(student=outside, lat="0", lng="0")


@pytest.mark.django_db
def test_false_signal_increments_abuse_and_eventually_suspends_student(signal, driver, bus, student):
    flagged = flag_false_signal(signal=signal, by=driver.user)
    assert flagged.status == SignalStatus.ANNULE
    assert flagged.flagged_false

    student.refresh_from_db()
    register_abuse_warning(student=student)
    student.refresh_from_db()
    assert student.abuse_warnings == 2
    assert student.signals_suspended_until > timezone.now()


@pytest.mark.django_db
def test_expiration_marks_stale_signals_inactive(signal):
    count = expire_stale_signals(now=timezone.now() + timedelta(hours=1))
    signal.refresh_from_db()

    assert count == 1
    assert signal.status == SignalStatus.EXPIRE
    assert signal.is_active is False


@pytest.mark.django_db
def test_student_can_cancel_own_signal(signal, student):
    cancelled = cancel_signal(signal=signal, by=student.user)

    assert cancelled.status == SignalStatus.ANNULE


@pytest.mark.django_db
def test_driver_closes_signal_when_bus_takes_student(signal, driver, bus):
    closed = close_signal(signal=signal, by=driver.user, bus=bus)

    assert closed.status == SignalStatus.PRIS_EN_CHARGE
    assert closed.taken_by_bus == bus
    assert closed.taken_at is not None


@pytest.mark.django_db
def test_signal_api_creates_signal_and_exposes_it_to_driver_and_admin(client, student, trajet, driver, bus, admin_user):
    client.force_login(student.user)

    response = client.post(
        "/api/signals/",
        data={"lat": "3.8667", "lng": "11.5167", "accuracy": 8},
        content_type="application/json",
    )

    assert response.status_code == 201
    signal = Signal.objects.get(pk=response.json()["id"])
    assert signal.status == SignalStatus.ACTIF
    assert signal.student == student
    assert signal.trajet == trajet

    for user in (driver.user, admin_user):
        client.force_login(user)
        visible = client.get("/api/signals/visible/")
        assert visible.status_code == 200
        assert str(signal.pk) in {str(item["id"]) for item in visible.json()["signals"]}


@pytest.mark.django_db
def test_signal_page_exposes_missing_consent_and_consent_endpoint(client, student):
    student.consent_location = False
    student.location_consent_at = None
    student.save(update_fields=["consent_location", "location_consent_at", "updated_at"])
    client.force_login(student.user)
    session = client.session
    session["otp_verified_at"] = 9_999_999_999
    session.save()

    page = client.get(reverse("signals:home"))
    assert page.status_code == 200
    assert 'data-location-consent="false"' in page.content.decode()

    consent = client.post("/api/users/consent/")
    assert consent.status_code == 200
    student.refresh_from_db()
    assert student.has_location_consent
