from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from estuairefleet.core.constants import DEFAULT_SIGNAL_LIFETIME

from .models import Signal, SignalStatus
from .selectors import get_active_signal_for_student
from .validators import validate_signal_position


def _queue_alert_evaluation(route):
    from estuairefleet.alerts.services import evaluate_route_alert  # noqa: PLC0415

    transaction.on_commit(lambda: evaluate_route_alert(route=route))


@transaction.atomic
def emit_signal(*, student, route, latitude, longitude) -> Signal:
    if student.role != "student" or student.is_suspended:
        raise PermissionDenied("Seuls les étudiants actifs peuvent émettre un signal.")
    profile = getattr(student, "student_profile", None)
    if not profile or not profile.consent_location:
        raise PermissionDenied("Le consentement de localisation est requis.")
    validate_signal_position(route=route, latitude=latitude, longitude=longitude)
    existing = get_active_signal_for_student(student)
    expires_at = timezone.now() + timedelta(
        minutes=route.signal_lifetime_minutes or DEFAULT_SIGNAL_LIFETIME.seconds // 60
    )
    if existing:
        existing.position_lat = latitude
        existing.position_lng = longitude
        existing.expires_at = expires_at
        existing.save(update_fields=["position_lat", "position_lng", "expires_at", "updated_at"])
        _queue_alert_evaluation(route)
        return existing
    signal = Signal.objects.create(
        student=student,
        route=route,
        position_lat=latitude,
        position_lng=longitude,
        expires_at=expires_at,
    )
    _queue_alert_evaluation(route)
    return signal


@transaction.atomic
def cancel_signal(*, signal: Signal, student) -> Signal:
    if signal.student_id != student.id:
        raise PermissionDenied("Vous ne pouvez annuler que votre propre signal.")
    signal.status = SignalStatus.CANCELLED
    signal.cancelled_at = timezone.now()
    signal.save(update_fields=["status", "cancelled_at", "updated_at"])
    return signal


@transaction.atomic
def take_over_route_signals(*, route_id) -> int:
    return (
        Signal.objects.select_for_update()
        .filter(route_id=route_id, status=SignalStatus.ACTIVE)
        .update(status=SignalStatus.TAKEN_OVER, taken_over_at=timezone.now())
    )
