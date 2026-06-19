from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from inspector.api import create_app
from tests.conftest import make_image_bytes


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as c:
        yield c


def test_root_redirects_to_docs(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (307, 308)
    assert response.headers["location"] == "/docs"


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["classifier_backend"] == "stub"


def test_inspect_then_fetch(client):
    files = {"file": ("panel.png", make_image_bytes(), "image/png")}
    response = client.post("/inspect", files=files)
    assert response.status_code == 200
    created = response.json()
    assert created["label"]
    assert created["image_name"] == "panel.png"

    fetched = client.get(f"/inspections/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == created["id"]

    listing = client.get("/inspections")
    assert listing.status_code == 200
    assert any(item["id"] == created["id"] for item in listing.json())


def test_inspect_rejects_non_image(client):
    files = {"file": ("note.txt", b"not an image", "text/plain")}
    response = client.post("/inspect", files=files)
    assert response.status_code == 400


def test_missing_inspection_returns_404(client):
    assert client.get("/inspections/999999").status_code == 404


def test_metrics_endpoint(client):
    client.post("/inspect", files={"file": ("p.png", make_image_bytes(), "image/png")})
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"inspector_inspections_total" in response.content


def test_inspect_runs_off_the_event_loop(client, monkeypatch):
    # The blocking inference must be handed to the threadpool, not run inline.
    import inspector.api as api_module

    real = api_module.run_in_threadpool
    seen = {}

    async def spy(func, *args, **kwargs):
        seen["offloaded"] = True
        return await real(func, *args, **kwargs)

    monkeypatch.setattr(api_module, "run_in_threadpool", spy)
    response = client.post(
        "/inspect", files={"file": ("p.png", make_image_bytes(), "image/png")}
    )
    assert response.status_code == 200
    assert seen.get("offloaded") is True


def test_inspect_rejects_oversized_upload(tmp_path):
    from inspector.config import Settings

    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'big.db'}", max_upload_bytes=10
    )
    with TestClient(create_app(settings)) as client:
        payload = make_image_bytes(size=(256, 256))  # any real PNG exceeds 10 bytes
        response = client.post("/inspect", files={"file": ("big.png", payload, "image/png")})
        assert response.status_code == 413
