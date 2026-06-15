from __future__ import annotations

import io

import pytest
from PIL import Image

from inspector.classifier import StubClassifier
from inspector.config import Settings
from inspector.db import Base, InspectionRepository, create_engine_and_session
from inspector.reporter import TemplateReporter
from inspector.service import InspectionService


def make_image_bytes(color=(120, 120, 120), size=(64, 64)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def settings(tmp_path) -> Settings:
    db_path = tmp_path / "test.db"
    return Settings(
        database_url=f"sqlite:///{db_path}",
        classifier_backend="stub",
        reporter_backend="template",
        storage_root=str(tmp_path / "incoming"),
    )


@pytest.fixture
def session_factory(settings):
    engine, factory = create_engine_and_session(settings.database_url)
    Base.metadata.create_all(engine)
    return factory


@pytest.fixture
def service(session_factory):
    session = session_factory()
    return InspectionService(
        classifier=StubClassifier(),
        reporter=TemplateReporter(),
        repository=InspectionRepository(session),
        model_backend="stub",
    )
