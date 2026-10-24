from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from estuairefleet.core.exceptions import InvalidBusTransition
from estuairefleet.fleet.models import BusStatus, Direction
from estuairefleet.fleet.services import (
    change_bus_status,
    create_bus,
    create_campus,
    create_trajet,
    set_bus_occupancy,
    update_bus_position,
)


@pytest.mark.django_db
def test_campus_and_trajet_are_created_with_their_domain_relations(campus, second_campus):
    route = create_trajet(
        name="Trajet de test",
        direction=Direction.RETOUR,
        itinerary=[[3.8667, 11.5167], [3.9000, 11.5500]],
        horaires=["07:00", "18:00"],
        days_of_week=[],
        campuses=[campus, second_campus],
        stops=[{"name": "Arrêt principal", "latitude": "3.8667", "longitude": "11.5167", "order": 1}],
    )

    assert route.direction == Direction.RETOUR
    assert list(route.campuses.order_by("code")) == [second_campus, campus]
    assert route.stops.get(order=1).name == "Arrêt principal"
    assert route.is_in_service()


@pytest.mark.django_db
def test_campus_rejects_invalid_coordinates():
    invalid = create_campus(
        name="Campus invalide",
        code="invalide",
        latitude=3.0,
        longitude=11.0,
    )
    invalid.latitude = 91

    with pytest.raises(ValidationError):
        invalid.full_clean()


@pytest.mark.django_db
def test_bus_links_driver_and_trajet_and_validates_capacity(driver, trajet):
    bus = create_bus(
        plate_number="CE-TEST-EF",
        label="Bus principal",
        capacity=40,
        chauffeur=driver,
        trajet=trajet,
        status=BusStatus.HORS_SERVICE,
    )

    assert bus.chauffeur == driver
    assert bus.trajet == trajet
    assert bus.free_seats == 40

    with pytest.raises(ValidationError):
        create_bus(plate_number="CE-BAD-EF", capacity=0, trajet=trajet)


@pytest.mark.django_db
def test_bus_status_transitions_and_occupancy_are_enforced(driver, trajet, bus_factory):
    bus = bus_factory(chauffeur=driver, status=BusStatus.HORS_SERVICE)

    change_bus_status(bus=bus, new_status=BusStatus.DISPONIBLE, by=driver.user)
    change_bus_status(bus=bus, new_status=BusStatus.EN_ROUTE, by=driver.user)
    full = set_bus_occupancy(bus=bus, places=bus.capacity, by=driver.user)
    available = set_bus_occupancy(bus=full, places=bus.capacity - 1, by=driver.user)

    assert available.status == BusStatus.DISPONIBLE
    assert available.places_occupees == bus.capacity - 1
    with pytest.raises(InvalidBusTransition):
        change_bus_status(bus=available, new_status=BusStatus.PLEIN, by=driver.user)


@pytest.mark.django_db
def test_bus_position_requires_its_driver_and_rejects_invalid_coordinates(bus, driver, admin_user):
    updated = update_bus_position(bus=bus, lat="3.8700", lng="11.5200", by=driver.user)
    updated.refresh_from_db()

    assert updated.position_lat == Decimal("3.8700")
    assert updated.position_lng == Decimal("11.5200")
    with pytest.raises(ValidationError):
        update_bus_position(bus=bus, lat=100, lng=11, by=admin_user)
