import pytest
from django.core.exceptions import PermissionDenied

from estuairefleet.core.exceptions import InvalidBusTransition
from estuairefleet.fleet.models import Bus, BusStatus, Trajet
from estuairefleet.fleet.services import change_bus_status, set_bus_occupancy, update_bus_position
from estuairefleet.signals.services import emit_signal
from estuairefleet.users.models import Chauffeur, Student, User


@pytest.mark.django_db
def test_bus_state_machine_and_full_bus_notification():
    route = Trajet.objects.create(name="Route état", itinerary=[[3.8667, 11.5167], [3.87, 11.52]])
    driver = User.objects.create_user(email="fleet-driver@example.test", password="password", role="driver")
    chauffeur = Chauffeur.objects.create(user=driver, licence_number="LIC-FLEET")
    bus = Bus.objects.create(plate_number="CE-FLEET", capacity=1, chauffeur=chauffeur, trajet=route)
    student_user = User.objects.create_user(email="fleet-student@example.test", password="password", role="student")
    student = Student.objects.create(user=student_user, consent_location=True)
    student.trajets_habituels.add(route)
    signal = emit_signal(student=student, trajet=route, lat=3.8667, lng=11.5167)

    bus = change_bus_status(bus=bus, new_status=BusStatus.DISPONIBLE, by=driver)
    bus = change_bus_status(bus=bus, new_status=BusStatus.EN_ROUTE, by=driver)
    bus = set_bus_occupancy(bus=bus, places=1, by=driver)

    assert bus.status == BusStatus.PLEIN
    assert student_user.notifications.filter(notification_type="bus_change").exists()
    with pytest.raises(InvalidBusTransition):
        change_bus_status(bus=bus, new_status=BusStatus.EN_ROUTE, by=driver)
    assert signal.status == "actif"


@pytest.mark.django_db
def test_bus_position_is_limited_to_its_driver_or_admin():
    driver = User.objects.create_user(email="position-driver@example.test", password="password", role="driver")
    other = User.objects.create_user(email="position-other@example.test", password="password", role="driver")
    chauffeur = Chauffeur.objects.create(user=driver, licence_number="LIC-POSITION")
    bus = Bus.objects.create(plate_number="CE-POSITION", capacity=20, chauffeur=chauffeur)

    with pytest.raises(PermissionDenied):
        update_bus_position(bus=bus, lat=3.8667, lng=11.5167, by=other)
    updated = update_bus_position(bus=bus, lat=3.8667, lng=11.5167, by=driver)

    assert updated.position_lat == 3.8667
