from datetime import timedelta

from django.core.cache import cache
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.utils import timezone

from estuairefleet.alerts.models import Alert, AlertStatus
from estuairefleet.fleet.models import Bus, BusStatus, Incident
from estuairefleet.signals.models import Signal, SignalStatus
from estuairefleet.users.models import Chauffeur, Student


def _calculate_operational_statistics():
    now = timezone.now()
    signal_stats = Signal.objects.aggregate(
        total=Count("id"),
        taken=Count("id", filter=Q(status=SignalStatus.PRIS_EN_CHARGE)),
        average_wait=Avg(ExpressionWrapper(F("taken_at") - F("created_at"), output_field=DurationField())),
    )
    average_wait = signal_stats["average_wait"]
    average_wait_minutes = average_wait / timedelta(minutes=1) if average_wait else 0
    total_signals = signal_stats["total"] or 0
    taken_signals = signal_stats["taken"] or 0
    return {
        "students": Student.objects.filter(user__is_active=True).count(),
        "drivers": Chauffeur.objects.filter(user__is_active=True).count(),
        "buses_in_service": Bus.objects.filter(
            status__in=(BusStatus.DISPONIBLE, BusStatus.EN_ROUTE, BusStatus.PLEIN)
        ).count(),
        "active_signals": Signal.objects.filter(status=SignalStatus.ACTIF, expires_at__gt=now).count(),
        "open_alerts": Alert.objects.filter(
            status__in=(
                AlertStatus.PENDING,
                AlertStatus.TRIGGERED,
                AlertStatus.IN_PROGRESS,
                AlertStatus.RELAY,
                AlertStatus.ESCALATED,
            )
        ).count(),
        "open_incidents": Incident.objects.filter(~Q(status="resolu")).count(),
        "average_wait_minutes": round(average_wait_minutes, 1),
        "taken_rate": round((taken_signals / total_signals) * 100, 1) if total_signals else 0,
    }


def get_operational_statistics():
    return cache.get_or_set("estuairefleet:dashboard:statistics:v1", _calculate_operational_statistics, timeout=15)
