import pytest
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone


def _login_with_otp(client, user):
    client.force_login(user)
    session = client.session
    session["otp_verified_at"] = 9_999_999_999
    session.save()


@pytest.mark.django_db
def test_admin_can_access_dashboard_and_students_are_forbidden(client, admin_user, student):
    _login_with_otp(client, admin_user)
    response = client.get(reverse("core:dashboard"))
    assert response.status_code == 200
    assert "Tableau de bord" in response.content.decode()

    _login_with_otp(client, student.user)
    client.raise_request_exception = False
    forbidden = client.get(reverse("core:dashboard"))
    assert forbidden.status_code == 403


@pytest.mark.django_db
def test_admin_live_supervision_returns_operational_snapshot(client, admin_user, bus):
    cache.clear()
    bus.position_lat = "3.8700"
    bus.position_lng = "11.5200"
    bus.position_updated_at = timezone.now()
    bus.save(update_fields=["position_lat", "position_lng", "position_updated_at", "updated_at"])
    _login_with_otp(client, admin_user)

    response = client.get(reverse("core:dashboard_live"))
    payload = response.json()

    assert response.status_code == 200
    assert {"generated_at", "statistics", "buses", "alerts", "incidents", "routes"} <= payload.keys()
    assert payload["statistics"]["buses_in_service"] == 1
    assert payload["buses"][0]["plate_number"] == bus.plate_number
    assert payload["buses"][0]["position_lat"] == 3.87
    assert payload["buses"][0]["position_lng"] == 11.52


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("export_type", "content_type"),
    [
        ("csv", "text/csv"),
        ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("pdf", "application/pdf"),
    ],
)
def test_admin_exports_operational_statistics(client, admin_user, export_type, content_type):
    cache.clear()
    _login_with_otp(client, admin_user)

    response = client.get(reverse("core:dashboard_export", kwargs={"export_type": export_type}))

    assert response.status_code == 200
    assert response["Content-Type"] == content_type
    assert response["Content-Disposition"].startswith("attachment;")
