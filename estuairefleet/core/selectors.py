from statistics import fmean

from django.db.models import Q
from django.utils import timezone

from estuairefleet.alerts.models import Alert, AlertStatus
from estuairefleet.fleet.models import Bus, BusStatus, Incident
from estuairefleet.signals.models import Signal, SignalStatus
from estuairefleet.users.models import Chauffeur, Student


def get_operational_statistics():
    taken = list(Signal.objects.filter(taken_at__isnull=False).values_list("created_at", "taken_at"))
    waits = [(taken_at - created_at).total_seconds() / 60 for created_at, taken_at in taken]
    total_signals = Signal.objects.count()
    taken_signals = Signal.objects.filter(status=SignalStatus.PRIS_EN_CHARGE).count()
    return {
        "students": Student.objects.filter(user__is_active=True).count(),
        "drivers": Chauffeur.objects.filter(user__is_active=True).count(),
        "buses_in_service": Bus.objects.filter(
            status__in=(BusStatus.DISPONIBLE, BusStatus.EN_ROUTE, BusStatus.PLEIN)
        ).count(),
        "active_signals": Signal.objects.filter(status=SignalStatus.ACTIF, expires_at__gt=timezone.now()).count(),
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
        "average_wait_minutes": round(fmean(waits), 1) if waits else 0,
        "taken_rate": round((taken_signals / total_signals) * 100, 1) if total_signals else 0,
    }
