from __future__ import annotations

from inspector.classifier import StubClassifier
from inspector.db import InspectionRepository
from inspector.pipeline import run_batch
from inspector.reporter import TemplateReporter
from inspector.service import InspectionService
from inspector.storage import LocalObjectStore
from tests.conftest import make_image_bytes


def test_run_batch_processes_directory(tmp_path, session_factory):
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    for i in range(3):
        (incoming / f"panel_{i}.png").write_bytes(make_image_bytes(color=(i * 40, i, 0)))
    (incoming / "notes.txt").write_text("ignored")  # non-image is skipped

    session = session_factory()
    service = InspectionService(
        StubClassifier(), TemplateReporter(), InspectionRepository(session), "stub"
    )
    store = LocalObjectStore(str(incoming))

    summary = run_batch(store, service)

    assert summary["processed"] == 3
    assert sum(summary["by_label"].values()) == 3
    assert len(InspectionRepository(session).list()) == 3


def test_run_batch_empty_store(tmp_path, session_factory):
    session = session_factory()
    service = InspectionService(
        StubClassifier(), TemplateReporter(), InspectionRepository(session), "stub"
    )
    summary = run_batch(LocalObjectStore(str(tmp_path / "nope")), service)
    assert summary == {"processed": 0, "defects": 0, "by_label": {}}
