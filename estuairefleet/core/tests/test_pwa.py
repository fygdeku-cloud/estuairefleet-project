import json
from datetime import timedelta
from pathlib import Path

import pytest
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from estuairefleet.fleet.models import Trajet
from estuairefleet.signals.models import Signal, SignalStatus
from estuairefleet.users.models import Student, User

from ..selectors import get_operational_statistics


@pytest.mark.django_db
def test_service_worker_is_served_at_root(client):
    response = client.get("/sw.js")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("application/javascript")
    assert b"estuairefleet-shell-v3" in b"".join(response.streaming_content)


def test_pwa_assets_are_present():
    static_root = Path(settings.APPS_DIR) / "static" / "pwa"

    assert (static_root / "manifest.json").is_file()
    assert (static_root / "service-worker.js").is_file()
    assert (static_root / "offline.html").is_file()
    assert (static_root / "icons" / "icon-192.png").is_file()
    assert (static_root / "icons" / "icon-512.png").is_file()
    assert (static_root / "icons" / "icon-192.svg").is_file()
    assert (static_root / "icons" / "icon-512.svg").is_file()

    manifest = json.loads((static_root / "manifest.json").read_text())
    assert {icon["sizes"] for icon in manifest["icons"]} >= {"192x192", "512x512"}
    assert all(icon["type"] == "image/png" for icon in manifest["icons"])


@pytest.mark.django_db
def test_base_template_declares_pwa_manifest(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"/static/pwa/manifest.json" in response.content
    assert b"apple-mobile-web-app-capable" in response.content


@pytest.mark.django_db
def test_operational_statistics_uses_database_aggregation_and_short_cache():
    cache.clear()
    user = User.objects.create_user(email="stats@example.test", password="password", role="student")
    student = Student.objects.create(user=user, consent_location=True)
    route = Trajet.objects.create(name="Route statistiques", itinerary=[[3.8667, 11.5167], [3.87, 11.52]])
    signal = Signal.objects.create(
        student=student,
        trajet=route,
        position_lat=3.8667,
        position_lng=11.5167,
        status=SignalStatus.PRIS_EN_CHARGE,
        expires_at=timezone.now() + timedelta(minutes=10),
        taken_at=timezone.now(),
    )
    signal.created_at = signal.taken_at - timedelta(minutes=8)
    signal.save(update_fields=["created_at"])

    statistics = get_operational_statistics()

    assert statistics["taken_rate"] == 100.0
    assert statistics["average_wait_minutes"] == 8.0
