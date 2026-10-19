from pathlib import Path

import pytest
from django.conf import settings


@pytest.mark.django_db
def test_service_worker_is_served_at_root(client):
    response = client.get("/sw.js")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("application/javascript")
    assert b"estuairefleet-shell-v1" in b"".join(response.streaming_content)


def test_pwa_assets_are_present():
    static_root = Path(settings.APPS_DIR) / "static" / "pwa"

    assert (static_root / "manifest.json").is_file()
    assert (static_root / "service-worker.js").is_file()
    assert (static_root / "offline.html").is_file()
    assert (static_root / "icons" / "icon-192.svg").is_file()
    assert (static_root / "icons" / "icon-512.svg").is_file()
