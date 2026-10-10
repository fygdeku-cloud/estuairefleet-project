import pytest

from estuairefleet.alerts.models import AlertStatus
from estuairefleet.alerts.services import evaluate_route_alert
from estuairefleet.fleet.models import Trajet
from estuairefleet.signals.services import emit_signal
from estuairefleet.users.models import Student, User

ALERT_THRESHOLD = 5


@pytest.mark.django_db
def test_alert_is_triggered_at_route_threshold():
    route = Trajet.objects.create(
        name="Route seuil",
        route_type="outbound",
        itinerary=[[3.8667, 11.5167]],
        alert_threshold=ALERT_THRESHOLD,
    )
    for index in range(ALERT_THRESHOLD):
        user = User.objects.create_user(
            email=f"etudiant-{index}@example.com",
            password="password",
            role="student",
        )
        Student.objects.create(user=user, consent_location=True)
        emit_signal(student=user, route=route, latitude=3.8667, longitude=11.5167)

    alert = evaluate_route_alert(route=route)

    assert alert is not None
    assert alert.status == AlertStatus.TRIGGERED
    assert alert.priority is True
    assert alert.signal_count == ALERT_THRESHOLD
