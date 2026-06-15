from __future__ import annotations

from PIL import Image

from inspector.classifier import Prediction
from inspector.db import InspectionRepository
from inspector.service import InspectionService


class _FixedClassifier:
    classes = ["Clean", "Physical-Damage"]

    def __init__(self, prediction):
        self._prediction = prediction

    def predict(self, image):
        return self._prediction


class _RecordingReporter:
    def __init__(self):
        self.calls = 0

    def generate(self, prediction):
        self.calls += 1
        return "report body"


def _image():
    return Image.new("RGB", (16, 16), (0, 0, 0))


def test_inspect_persists_record(service):
    record = service.inspect(_image(), source="api", image_name="panel.png")
    assert record.id is not None
    assert record.source == "api"
    assert record.image_name == "panel.png"
    assert record.latency_ms >= 0


def test_defect_triggers_report_clean_does_not(session_factory):
    session = session_factory()
    repo = InspectionRepository(session)
    reporter = _RecordingReporter()

    defect_service = InspectionService(
        _FixedClassifier(Prediction("Physical-Damage", 88.0, {})), reporter, repo
    )
    rec = defect_service.inspect(_image(), source="api")
    assert rec.is_defect is True
    assert rec.report == "report body"
    assert reporter.calls == 1

    clean_service = InspectionService(
        _FixedClassifier(Prediction("Clean", 97.0, {})), reporter, repo
    )
    rec = clean_service.inspect(_image(), source="api")
    assert rec.is_defect is False
    assert rec.report is None
    assert reporter.calls == 1  # reporter not called again for a clean panel
