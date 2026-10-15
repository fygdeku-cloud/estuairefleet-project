from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import CoursInterCampus, IntercampusCourseStatus
from .services import notify_upcoming_course, send_course_reminder


@shared_task
def notify_upcoming_courses():
    now = timezone.now()
    courses = CoursInterCampus.objects.filter(
        status__in=(IntercampusCourseStatus.PLANNED, IntercampusCourseStatus.CONFIRMED),
        horaire_fin__lte=now + timedelta(minutes=60),
        horaire_fin__gte=now,
        bus_affecte__chauffeur__isnull=False,
    )
    count = 0
    for course in courses:
        if (
            course.horaire_fin <= now + timedelta(minutes=course.notify_before_minutes)
            and not course.driver_notified_at
        ):
            notify_upcoming_course(course=course)
            count += 1
        elif (
            course.driver_notified_at
            and not course.reminder_sent_at
            and course.horaire_fin <= now + timedelta(minutes=10)
        ):
            send_course_reminder(course=course)
            count += 1
    return count
