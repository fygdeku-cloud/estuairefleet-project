from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from estuairefleet.fleet.models import Bus, BusStatus, Campus
from estuairefleet.intercampus.models import IntercampusCourseStatus
from estuairefleet.intercampus.services import (
    assign_bus,
    auto_assign_bus,
    create_course,
    mark_driver_notified,
    transition_course,
)
from estuairefleet.users.models import Chauffeur, User


def campuses():
    return (
        Campus.objects.create(name="Campus A", code="campus-a", latitude=3.8667, longitude=11.5167),
        Campus.objects.create(name="Campus B", code="campus-b", latitude=3.87, longitude=11.52),
    )


@pytest.mark.django_db
def test_course_validation_transition_and_driver_notification():
    depart, arrivee = campuses()
    driver = User.objects.create_user(email="inter-driver@example.test", password="password", role="driver")
    chauffeur = Chauffeur.objects.create(user=driver, licence_number="LIC-INTER")
    bus = Bus.objects.create(plate_number="CE-INTER", capacity=30, status=BusStatus.DISPONIBLE, chauffeur=chauffeur)
    start = timezone.now() + timedelta(hours=2)
    course = create_course(
        group="L2 Informatique",
        campus_depart=depart,
        campus_arrivee=arrivee,
        start_at=start,
        horaire_fin=start + timedelta(hours=1),
        effectif=25,
    )
    assign_bus(course=course, bus=bus)
    transition_course(course=course, target=IntercampusCourseStatus.CONFIRMED)
    mark_driver_notified(course=course)

    course.refresh_from_db()
    assert course.status == IntercampusCourseStatus.CONFIRMED
    assert course.driver_notified_at is not None
    notification = driver.notifications.get(title="Cours inter-campus planifié")
    assert notification.notification_type == "intercampus"


@pytest.mark.django_db
def test_bus_cannot_be_double_booked_on_overlapping_courses():
    depart, arrivee = campuses()
    driver = User.objects.create_user(email="inter-driver-2@example.test", password="password", role="driver")
    chauffeur = Chauffeur.objects.create(user=driver, licence_number="LIC-INTER-2")
    bus = Bus.objects.create(plate_number="CE-INTER-2", capacity=30, status=BusStatus.DISPONIBLE, chauffeur=chauffeur)
    start = timezone.now() + timedelta(hours=2)
    first = create_course(
        group="G1",
        campus_depart=depart,
        campus_arrivee=arrivee,
        start_at=start,
        horaire_fin=start + timedelta(hours=1),
    )
    second = create_course(
        group="G2",
        campus_depart=depart,
        campus_arrivee=arrivee,
        start_at=start + timedelta(minutes=30),
        horaire_fin=start + timedelta(hours=2),
    )
    assign_bus(course=first, bus=bus)

    with pytest.raises(ValidationError):
        assign_bus(course=second, bus=bus)


@pytest.mark.django_db
def test_course_can_assign_the_first_compatible_available_bus():
    depart, arrivee = campuses()
    driver = User.objects.create_user(email="auto-driver@example.test", password="password", role="driver")
    chauffeur = Chauffeur.objects.create(user=driver, licence_number="LIC-AUTO")
    bus = Bus.objects.create(plate_number="CE-AUTO", capacity=40, status=BusStatus.DISPONIBLE, chauffeur=chauffeur)
    course = create_course(
        group="G auto",
        campus_depart=depart,
        campus_arrivee=arrivee,
        start_at=timezone.now() + timedelta(hours=2),
        horaire_fin=timezone.now() + timedelta(hours=3),
        effectif=20,
    )

    assigned = auto_assign_bus(course=course)

    assert assigned.bus_affecte_id == bus.pk
