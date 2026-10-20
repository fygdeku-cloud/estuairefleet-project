from django.db.models import Count, Q
from django.utils import timezone

from estuairefleet.core.geo import distance_point_to_polyline_m, haversine_m
from estuairefleet.fleet.models import Trajet

from .models import Signal, SignalStatus


def _student_profile(student):
    return student.student if hasattr(student, "student") else student


def get_active_signal_for_student(student):
    profile = _student_profile(student)
    return (
        Signal.objects.filter(student=profile, status=SignalStatus.ACTIF, expires_at__gt=timezone.now())
        .select_related("trajet")
        .first()
    )


def get_student_signal_history(student, limit=20):
    profile = _student_profile(student)
    return Signal.objects.filter(student=profile).select_related("trajet").order_by("-created_at")[:limit]


def get_active_signals_for_trajet(trajet):
    return Signal.objects.filter(
        trajet=trajet, status=SignalStatus.ACTIF, expires_at__gt=timezone.now()
    ).select_related("student__user", "trajet")


def get_active_signals_for_route(route_id):
    """Alias compatible avec un objet trajet ou son identifiant."""
    trajet = route_id if hasattr(route_id, "pk") else Trajet.objects.get(pk=route_id)
    return get_active_signals_for_trajet(trajet)


def get_visible_signals_for(user, *, since=None):
    now = timezone.now()
    queryset = Signal.objects.filter(status=SignalStatus.ACTIF, expires_at__gt=now).select_related(
        "student__user", "trajet", "student__campus"
    )
    if user.role == "student":
        queryset = queryset.filter(student__user=user)
    own_trajet_id = None
    if user.role == "driver":
        bus = getattr(getattr(user, "chauffeur", None), "bus", None)
        own_trajet_id = bus.trajet_id if bus else None
        queryset = queryset.filter(trajet_id=own_trajet_id) if own_trajet_id else queryset.none()
    if since is not None:
        queryset = queryset.filter(updated_at__gt=since)
    payload = []
    for signal in queryset:
        if user.role in {"admin", "administrator"}:
            label = signal.student.user.get_full_name() or signal.student.user.matricule or "Étudiant"
        elif user.role == "staff":
            label = f"Étudiant #{str(signal.student.user_id).replace('-', '')[:4].upper()}"
        elif user.role == "driver":
            label = signal.student.user.get_full_name() or "Étudiant"
        else:
            label = "Vous"
        payload.append(
            {
                "id": signal.id,
                "lat": float(signal.position_lat),
                "lng": float(signal.position_lng),
                "trajet_id": signal.trajet_id,
                "trajet_name": signal.trajet.name,
                "age_seconds": signal.age_seconds,
                "expires_in_seconds": signal.seconds_left,
                "priority": bool(own_trajet_id and signal.trajet_id == own_trajet_id),
                "student_label": label,
                "student_id": signal.student_id if user.role in {"admin", "administrator"} else None,
                "signal": signal,
                "updated_at": signal.updated_at,
            }
        )
    return sorted(payload, key=lambda item: (not item["priority"], item["age_seconds"]))


def count_active_signals(trajet):
    return get_active_signals_for_trajet(trajet).count()


def get_active_signals_by_trajet():
    rows = (
        Signal.objects.filter(status=SignalStatus.ACTIF, expires_at__gt=timezone.now())
        .values("trajet_id")
        .order_by()
        .annotate(count=Count("id"))
    )
    return {row["trajet_id"]: row["count"] for row in rows}


def resolve_trajet_for_position(student, lat, lng, now=None):
    profile = _student_profile(student)
    point = (float(lat), float(lng))
    usual_trajet_ids = set(profile.trajets_habituels.values_list("pk", flat=True)) if profile else set()
    candidates = []
    for trajet in Trajet.objects.filter(is_active=True).prefetch_related("stops", "campuses"):
        if not trajet.is_in_service(now):
            continue
        distances = [distance_point_to_polyline_m(point, trajet.polyline)]
        distances.extend(haversine_m(point, stop.point) for stop in trajet.stops.all())
        distances.extend(haversine_m(point, campus.point) for campus in trajet.campuses.all())
        distance = min(distances)
        if distance <= trajet.geofence_radius_m:
            usual = trajet.pk in usual_trajet_ids
            candidates.append((not usual, distance, trajet))
    candidates.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in candidates]


def get_students_with_abuse():
    from estuairefleet.users.models import Student

    return Student.objects.select_related("user").filter(
        Q(abuse_warnings__gt=0) | Q(signals_suspended_until__gt=timezone.now())
    )
