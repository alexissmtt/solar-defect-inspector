from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from inspector.api import create_app
from tests.conftest import make_image_bytes


@pytest.fixture
def client(settings):
    return TestClient(create_app(settings))


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
