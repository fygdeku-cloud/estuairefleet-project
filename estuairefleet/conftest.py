from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def media_storage(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
