import pytest
from rest_framework.test import APIClient

from estuairefleet.fleet.models import Trajet
from estuairefleet.signals.services import emit_signal
from estuairefleet.users.models import Student, User


@pytest.mark.django_db
def test_student_cannot_access_visible_signal_endpoint():
    user = User.objects.create_user(email="privacy@example.test", password="password", role="student")
    Student.objects.create(user=user, consent_location=True)
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/signals/visible/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_staff_visible_payload_contains_signal_without_exposing_to_student_endpoint():
    route = Trajet.objects.create(name="Route privacy", itinerary=[[3.8667, 11.5167], [3.87, 11.52]])
    student = User.objects.create_user(email="privacy-student@example.test", password="password", role="student")
    Student.objects.create(user=student, consent_location=True)
    emit_signal(student=student, trajet=route, lat=3.8667, lng=11.5167)
    staff = User.objects.create_user(email="privacy-staff@example.test", password="password", role="staff")
    client = APIClient()
    client.force_authenticate(user=staff)

    response = client.get("/api/signals/visible/")

    assert response.status_code == 200
    assert response.json()["signals"][0]["student_label"].startswith("Étudiant #")
