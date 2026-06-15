from __future__ import annotations

from inspector.classifier import Prediction
from inspector.config import Settings
from inspector.reporter import TemplateReporter, build_reporter


def test_template_report_contains_key_fields():
    report = TemplateReporter().generate(Prediction("Electrical-damage", 91.2, {}))
    assert "Electrical-damage" in report
    assert "Severity: High" in report
    assert "Recommended action" in report
    assert "production loss" in report.lower()


def test_build_reporter_falls_back_without_key():
    # reporter_backend=groq but no API key -> graceful fallback to template
    reporter = build_reporter(Settings(reporter_backend="groq", groq_api_key=None))
    assert isinstance(reporter, TemplateReporter)
