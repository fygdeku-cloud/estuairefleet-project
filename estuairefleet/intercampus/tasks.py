from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import CoursInterCampus, IntercampusCourseStatus
from .services import notify_upcoming_course


@shared_task
def notify_upcoming_courses():
    now = timezone.now()
    courses = CoursInterCampus.objects.filter(
        status__in=(IntercampusCourseStatus.PLANNED, IntercampusCourseStatus.CONFIRMED),
        driver_notified_at__isnull=True,
        start_at__lte=now + timedelta(minutes=60),
        start_at__gte=now,
        bus_affecte__chauffeur__isnull=False,
    )
    count = 0
    for course in courses:
        if course.start_at <= now + timedelta(minutes=course.notify_before_minutes):
            notify_upcoming_course(course=course)
            count += 1
    return count
