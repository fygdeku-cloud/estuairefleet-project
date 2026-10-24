from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError

from estuairefleet.intercampus.models import IntercampusCourseStatus
from estuairefleet.intercampus.services import (
    assign_bus,
    create_course,
    mark_driver_notified,
    send_course_reminder,
    transition_course,
)


@pytest.mark.django_db
def test_course_is_created_and_follows_allowed_status_transitions(intercampus_course):
    confirmed = transition_course(course=intercampus_course, target=IntercampusCourseStatus.CONFIRMED)
    completed = transition_course(course=confirmed, target=IntercampusCourseStatus.COMPLETED)

    assert completed.status == IntercampusCourseStatus.COMPLETED
    with pytest.raises(ValidationError):
        transition_course(course=completed, target=IntercampusCourseStatus.CANCELLED)


@pytest.mark.django_db
def test_bus_assignment_rejects_overlapping_courses(intercampus_course, campus, second_campus):
    conflicting = create_course(
        group="Groupe en conflit",
        campus_depart=campus,
        campus_arrivee=second_campus,
        start_at=intercampus_course.start_at + timedelta(minutes=15),
        horaire_fin=intercampus_course.horaire_fin + timedelta(minutes=15),
        effectif=10,
    )

    with pytest.raises(ValidationError):
        assign_bus(course=conflicting, bus=intercampus_course.bus_affecte)


@pytest.mark.django_db
def test_driver_notification_and_reminder_are_recorded(intercampus_course):
    notified = mark_driver_notified(course=intercampus_course)
    reminded = send_course_reminder(course=notified)
    reminded.refresh_from_db()

    assert reminded.driver_notified_at is not None
    assert reminded.reminder_sent_at is not None
    assert reminded.bus_affecte.chauffeur.user.notifications.filter(notification_type="intercampus").count() == 2
