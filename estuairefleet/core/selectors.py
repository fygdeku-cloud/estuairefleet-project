from datetime import timedelta

from django.core.cache import cache
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.utils import timezone

from estuairefleet.alerts.models import Alert, AlertStatus
from estuairefleet.fleet.models import Bus, BusStatus, Incident, IncidentStatus, Trajet
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


def get_supervision_snapshot():
    def build_snapshot():
        open_alerts = (
            Alert.objects.filter(
                status__in=(
                    AlertStatus.PENDING,
                    AlertStatus.TRIGGERED,
                    AlertStatus.IN_PROGRESS,
                    AlertStatus.RELAY,
                    AlertStatus.ESCALATED,
                )
            )
            .select_related("route")
            .order_by("-priority", "created_at")[:8]
        )
        open_incidents = (
            Incident.objects.exclude(status=IncidentStatus.RESOLU)
            .select_related("bus", "trajet")
            .order_by("-reported_at")[:8]
        )
        routes = (
            Trajet.objects.filter(is_active=True)
            .annotate(
                bus_count=Count("buses", distinct=True),
                active_signal_count=Count("signals", filter=Q(signals__status=SignalStatus.ACTIF), distinct=True),
            )
            .order_by("name")[:12]
        )
        buses = Bus.objects.filter(position_lat__isnull=False, position_lng__isnull=False).values(
            "id", "plate_number", "status", "position_lat", "position_lng", "position_updated_at", "trajet__name"
        )[:100]
        return {
            "generated_at": timezone.now().isoformat(),
            "statistics": get_operational_statistics(),
            "buses": [
                {
                    **bus,
                    "id": str(bus["id"]),
                    "position_lat": float(bus["position_lat"]),
                    "position_lng": float(bus["position_lng"]),
                    "position_updated_at": bus["position_updated_at"].isoformat()
                    if bus["position_updated_at"]
                    else None,
                }
                for bus in buses
            ],
            "alerts": [
                {
                    "id": str(alert.pk),
                    "route": alert.route.name,
                    "status": alert.get_status_display(),
                    "signal_count": alert.signal_count,
                    "priority": alert.priority,
                }
                for alert in open_alerts
            ],
            "incidents": [
                {
                    "id": str(incident.pk),
                    "type": incident.get_type_display(),
                    "status": incident.get_status_display(),
                    "description": incident.description,
                    "bus": incident.bus.plate_number if incident.bus else "Bus non renseigné",
                }
                for incident in open_incidents
            ],
            "routes": [
                {
                    "id": str(route.pk),
                    "name": route.name,
                    "buses": route.bus_count,
                    "signals": route.active_signal_count,
                }
                for route in routes
            ],
        }

    return cache.get_or_set("estuairefleet:supervision:snapshot:v1", build_snapshot, timeout=5)
