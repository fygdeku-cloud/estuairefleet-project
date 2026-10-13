from django.db.models import QuerySet
from django.utils import timezone

from .models import CoursInterCampus, IntercampusCourseStatus


def get_upcoming_courses() -> QuerySet[CoursInterCampus]:
    return (
        CoursInterCampus.objects.filter(
            status__in=(IntercampusCourseStatus.PLANNED, IntercampusCourseStatus.CONFIRMED),
            start_at__gte=timezone.now(),
        )
        .select_related("campus_depart", "campus_arrivee", "bus_affecte__chauffeur__user")
        .order_by("start_at")
    )


def get_manageable_courses() -> QuerySet[CoursInterCampus]:
    return CoursInterCampus.objects.select_related("campus_depart", "campus_arrivee", "bus_affecte").order_by(
        "start_at"
    )


def get_course_detail(course_id) -> CoursInterCampus:
    return CoursInterCampus.objects.select_related(
        "campus_depart", "campus_arrivee", "bus_affecte__chauffeur__user"
    ).get(pk=course_id)
