import pytest


@pytest.mark.django_db
def test_user_and_transport_fixtures_are_composable(student, driver, bus, signal, alert):
    assert student.user.role == "student"
    assert driver.user.role == "driver"
    assert bus.chauffeur == driver
    assert signal.student == student
    assert alert.route == signal.trajet


@pytest.mark.django_db
def test_remaining_domain_fixtures_are_composable(intercampus_course, bus, notification, student):
    assert intercampus_course.bus_affecte == bus
    assert notification.recipient == student.user
