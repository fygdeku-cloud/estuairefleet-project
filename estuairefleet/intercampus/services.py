from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from estuairefleet.fleet.models import Bus, BusStatus
from estuairefleet.notifications.services import create_in_app_notification

from .models import CourseChangeType, CoursInterCampus, IntercampusCourseStatus
from .validators import validate_course_status_transition


@transaction.atomic
def create_course(**data) -> CoursInterCampus:
    course = CoursInterCampus(**data)
    course.full_clean()
    course.save()
    return course


@transaction.atomic
def update_course(*, course: CoursInterCampus, **data) -> CoursInterCampus:
    locked = CoursInterCampus.objects.select_for_update().get(pk=course.pk)
    schedule_changed = any(key in data for key in ("start_at", "horaire_fin", "bus_affecte", "status"))
    for key, value in data.items():
        setattr(locked, key, value)
    locked.full_clean()
    if schedule_changed:
        locked.last_changed_at = timezone.now()
        locked.driver_notified_at = None
        locked.reminder_sent_at = None
        if locked.status != IntercampusCourseStatus.CANCELLED:
            locked.change_type = CourseChangeType.EXTENDED if "horaire_fin" in data else CourseChangeType.ADVANCED
    locked.save()
    return locked


@transaction.atomic
def assign_bus(*, course: CoursInterCampus, bus) -> CoursInterCampus:
    locked = CoursInterCampus.objects.select_for_update().get(pk=course.pk)
    conflict = (
        CoursInterCampus.objects.filter(
            bus_affecte=bus,
            status__in=(IntercampusCourseStatus.PLANNED, IntercampusCourseStatus.CONFIRMED),
            start_at__lt=locked.horaire_fin,
            horaire_fin__gt=locked.start_at,
        )
        .exclude(pk=locked.pk)
        .exists()
    )
    if conflict:
        raise ValidationError("Ce bus est déjà affecté à un autre cours sur cette plage.")
    locked.bus_affecte = bus
    locked.driver_notified_at = None
    locked.full_clean()
    locked.save(update_fields=["bus_affecte", "driver_notified_at", "updated_at"])
    return locked


@transaction.atomic
def auto_assign_bus(*, course: CoursInterCampus) -> CoursInterCampus:
    locked = CoursInterCampus.objects.select_for_update().get(pk=course.pk)
    candidates = Bus.objects.filter(
        status__in=(BusStatus.DISPONIBLE, BusStatus.EN_ROUTE),
        chauffeur__isnull=False,
        capacity__gte=locked.effectif,
    ).order_by("places_occupees", "plate_number")
    for bus in candidates:
        try:
            return assign_bus(course=locked, bus=bus)
        except ValidationError:
            continue
    raise ValidationError("Aucun bus disponible ne peut être affecté à ce cours.")


@transaction.atomic
def transition_course(*, course: CoursInterCampus, target: str) -> CoursInterCampus:
    locked = CoursInterCampus.objects.select_for_update().get(pk=course.pk)
    validate_course_status_transition(current=locked.status, target=target)
    locked.status = target
    locked.save(update_fields=["status", "updated_at"])
    return locked


@transaction.atomic
def mark_driver_notified(*, course: CoursInterCampus) -> CoursInterCampus:
    locked = (
        CoursInterCampus.objects.select_for_update().select_related("bus_affecte__chauffeur__user").get(pk=course.pk)
    )
    if not locked.bus_affecte or not locked.bus_affecte.chauffeur:
        raise ValidationError("Un bus avec chauffeur doit être affecté avant la notification.")
    locked.driver_notified_at = timezone.now()
    locked.reminder_sent_at = None
    locked.save(update_fields=["driver_notified_at", "reminder_sent_at", "updated_at"])
    create_in_app_notification(
        recipient=locked.bus_affecte.chauffeur.user,
        title="Cours inter-campus planifié",
        message=f"Le cours {locked.group} commence le {locked.start_at:%d/%m à %H:%M}.",
        metadata={"course_id": str(locked.pk)},
    )
    return locked


@transaction.atomic
def notify_upcoming_course(*, course: CoursInterCampus) -> CoursInterCampus:
    if course.driver_notified_at:
        return course
    return mark_driver_notified(course=course)


@transaction.atomic
def send_course_reminder(*, course: CoursInterCampus) -> CoursInterCampus:
    locked = (
        CoursInterCampus.objects.select_for_update().select_related("bus_affecte__chauffeur__user").get(pk=course.pk)
    )
    if locked.reminder_sent_at or not locked.bus_affecte or not locked.bus_affecte.chauffeur:
        return locked
    locked.reminder_sent_at = timezone.now()
    locked.save(update_fields=["reminder_sent_at", "updated_at"])
    create_in_app_notification(
        recipient=locked.bus_affecte.chauffeur.user,
        title="Rappel de cours inter-campus",
        message=f"Le déplacement du groupe {locked.group} approche.",
        metadata={"course_id": str(locked.pk), "reminder": True},
    )
    return locked


@transaction.atomic
def change_course_schedule(*, course, start_at=None, horaire_fin=None, note=""):
    data = {"change_note": note}
    if start_at is not None:
        data["start_at"] = start_at
    if horaire_fin is not None:
        data["horaire_fin"] = horaire_fin
    return update_course(course=course, **data)


@transaction.atomic
def delete_course(*, course: CoursInterCampus) -> None:
    course.delete()
