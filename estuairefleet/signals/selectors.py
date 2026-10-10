from django.db.models import QuerySet
from django.utils import timezone

from .models import Signal, SignalStatus


def get_active_signals_for_route(route_id) -> QuerySet[Signal]:
    return Signal.objects.filter(
        route_id=route_id,
        status=SignalStatus.ACTIVE,
        expires_at__gt=timezone.now(),
    ).select_related("student", "route")


def get_active_signal_for_student(student) -> Signal | None:
    return (
        Signal.objects.filter(
            student=student,
            status=SignalStatus.ACTIVE,
            expires_at__gt=timezone.now(),
        )
        .select_related("route")
        .first()
    )
