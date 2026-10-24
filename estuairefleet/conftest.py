from __future__ import annotations

from datetime import timedelta
from itertools import count

import pytest
from django.utils import timezone

from estuairefleet.alerts.models import Alert, AlertStatus
from estuairefleet.fleet.models import Bus, BusStatus, Campus, Direction, Trajet
from estuairefleet.intercampus.models import CoursInterCampus
from estuairefleet.notifications.models import Notification, NotificationStatus
from estuairefleet.signals.models import Signal, SignalStatus
from estuairefleet.users.models import Chauffeur, Student, User, UserRole


@pytest.fixture(autouse=True)
def media_storage(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)


@pytest.fixture
def user_factory(db):
    sequence = count(1)

    def make_user(*, role=UserRole.STUDENT, email=None, matricule=None, **extra_fields):
        number = next(sequence)
        return User.objects.create_user(
            email=email or f"{role}-{number}@example.test",
            password="UneBonnePhraseDePasse!2026",
            role=role,
            matricule=matricule,
            must_change_password=False,
            first_name=extra_fields.pop("first_name", "Utilisateur"),
            last_name=extra_fields.pop("last_name", str(number)),
            **extra_fields,
        )

    return make_user


@pytest.fixture
def campus(db):
    return Campus.objects.create(
        name="Campus principal",
        code="principal",
        address="Yaoundé",
        latitude="3.8667",
        longitude="11.5167",
        radius_m=500,
    )


@pytest.fixture
def second_campus(db):
    return Campus.objects.create(
        name="Campus annexe",
        code="annexe",
        address="Yaoundé",
        latitude="3.9000",
        longitude="11.5500",
        radius_m=500,
    )


@pytest.fixture
def trajet(db, campus):
    route = Trajet.objects.create(
        name="Campus principal — Campus annexe",
        direction=Direction.ALLER,
        itinerary=[[3.8667, 11.5167], [3.9000, 11.5500]],
        horaires=["07:00", "18:00"],
        days_of_week=[],
        seuil_alerte=5,
        signal_ttl_minutes=20,
        geofence_radius_m=500,
    )
    route.campuses.add(campus)
    return route


@pytest.fixture
def student_factory(db, user_factory, campus, trajet):
    sequence = count(1)

    def make_student(*, user=None, matricule=None, consent=True):
        number = next(sequence)
        matricule = matricule or (user.matricule if user else None) or f"INS-2026-{number:03d}"
        user = user or user_factory(role=UserRole.STUDENT, matricule=matricule)
        profile = Student.objects.create(
            user=user,
            matricule=matricule,
            campus=campus,
            consent_location=consent,
            location_consent_at=timezone.now() if consent else None,
        )
        profile.trajets_habituels.add(trajet)
        return profile

    return make_student


@pytest.fixture
def student(student_factory):
    return student_factory()


@pytest.fixture
def driver_factory(db, user_factory):
    def make_driver(*, user=None, licence_number=None):
        user = user or user_factory(role=UserRole.DRIVER)
        return Chauffeur.objects.create(
            user=user,
            licence_number=licence_number or f"LIC-{user.pk.hex[:8].upper()}",
        )

    return make_driver


@pytest.fixture
def driver(driver_factory):
    return driver_factory()


@pytest.fixture
def admin_user(user_factory):
    return user_factory(role=UserRole.ADMIN)


@pytest.fixture
def staff_user(user_factory):
    return user_factory(role=UserRole.STAFF)


@pytest.fixture
def bus_factory(db, trajet, driver_factory):
    sequence = count(1)

    def make_bus(*, chauffeur=None, status=BusStatus.DISPONIBLE, **fields):
        number = next(sequence)
        return Bus.objects.create(
            plate_number=fields.pop("plate_number", f"CE-{number}-EF"),
            label=fields.pop("label", "Bus de test"),
            capacity=fields.pop("capacity", 40),
            status=status,
            chauffeur=chauffeur or driver_factory(),
            trajet=fields.pop("trajet", trajet),
            **fields,
        )

    return make_bus


@pytest.fixture
def bus(bus_factory, driver):
    return bus_factory(chauffeur=driver)


@pytest.fixture
def signal(db, student, trajet):
    return Signal.objects.create(
        student=student,
        trajet=trajet,
        position_lat="3.8667",
        position_lng="11.5167",
        accuracy_m=10,
        status=SignalStatus.ACTIF,
        expires_at=timezone.now() + timedelta(minutes=20),
    )


@pytest.fixture
def alert(db, trajet):
    return Alert.objects.create(
        route=trajet,
        threshold=5,
        signal_count=5,
        priority=True,
        status=AlertStatus.TRIGGERED,
        triggered_at=timezone.now(),
        response_deadline=timezone.now() + timedelta(minutes=3),
    )


@pytest.fixture
def intercampus_course(db, campus, second_campus, bus):
    start_at = timezone.now() + timedelta(hours=2)
    return CoursInterCampus.objects.create(
        group="L3 Informatique",
        campus_depart=campus,
        campus_arrivee=second_campus,
        start_at=start_at,
        horaire_fin=start_at + timedelta(hours=2),
        effectif=30,
        bus_affecte=bus,
    )


@pytest.fixture
def notification(db, student_user):
    return Notification.objects.create(
        recipient=student_user,
        title="Information de test",
        message="Message de test",
        status=NotificationStatus.SENT,
        sent_at=timezone.now(),
    )


@pytest.fixture
def student_user(student):
    return student.user
