from django.db import transaction
from django.utils import timezone

from .models import CoursInterCampus


@transaction.atomic
def assign_bus(*, course: CoursInterCampus, bus) -> CoursInterCampus:
    course.bus_affecte = bus
    course.driver_notified_at = None
    course.save(update_fields=["bus_affecte", "driver_notified_at", "updated_at"])
    return course


@transaction.atomic
def mark_driver_notified(*, course: CoursInterCampus) -> CoursInterCampus:
    course.driver_notified_at = timezone.now()
    course.save(update_fields=["driver_notified_at", "updated_at"])
    return course
