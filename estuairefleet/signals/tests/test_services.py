from datetime import timedelta

import pytest
from django.utils import timezone

from estuairefleet.fleet.models import Trajet
from estuairefleet.signals.models import SignalStatus
from estuairefleet.signals.services import emit_signal
from estuairefleet.users.models import Student, User


@pytest.mark.django_db
def test_emit_signal_updates_existing_active_signal():
    student_user = User.objects.create_user(
        email="etudiant@example.com",
        password="password",
        role="student",
    )
    Student.objects.create(user=student_user, consent_location=True)
    route = Trajet.objects.create(
        name="Route test",
        route_type="outbound",
        itinerary=[[3.8667, 11.5167]],
        signal_lifetime_minutes=20,
    )

    first = emit_signal(student=student_user, route=route, latitude=3.8667, longitude=11.5167)
    second = emit_signal(student=student_user, route=route, latitude=3.8668, longitude=11.5168)

    assert first.pk == second.pk
    assert second.status == SignalStatus.ACTIF
    assert second.expires_at > timezone.now() + timedelta(minutes=19)
