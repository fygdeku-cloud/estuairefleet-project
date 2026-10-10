from django.db.models import QuerySet
from django.utils import timezone

from .models import CoursInterCampus, IntercampusCourseStatus


def get_upcoming_courses() -> QuerySet[CoursInterCampus]:
    return CoursInterCampus.objects.filter(
        status__in=(IntercampusCourseStatus.PLANNED, IntercampusCourseStatus.CONFIRMED),
        start_at__gte=timezone.now(),
    ).select_related("campus_depart", "campus_arrivee", "bus_affecte", "bus_affecte__driver")
