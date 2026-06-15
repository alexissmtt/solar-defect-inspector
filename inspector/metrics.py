"""Prometheus metrics, exposed at /metrics.

These are what makes model behaviour observable in production: how many
inspections ran, how many were defects, the latency distribution and the
confidence of the most recent prediction. A drop in average confidence or a
shift in the class mix is an early signal of data drift.
"""

from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from .classifier import Prediction

INSPECTIONS = Counter(
    "inspector_inspections_total",
    "Total inspections processed",
    ["label", "source"],
)
DEFECTS = Counter(
    "inspector_defects_total",
    "Inspections classified as a defect",
    ["label"],
)
LATENCY = Histogram(
    "inspector_latency_ms",
    "End-to-end inspection latency in milliseconds",
    buckets=(5, 10, 25, 50, 100, 250, 500, 1000, 2500),
)
LAST_CONFIDENCE = Gauge(
    "inspector_last_confidence_percent",
    "Confidence of the most recent prediction",
)


def record(prediction: Prediction, source: str, latency_ms: float) -> None:
    INSPECTIONS.labels(label=prediction.label, source=source).inc()
    if prediction.is_defect:
        DEFECTS.labels(label=prediction.label).inc()
    LATENCY.observe(latency_ms)
    LAST_CONFIDENCE.set(prediction.confidence)


def render() -> tuple:
    """Return (payload, content_type) for the /metrics endpoint."""
    return generate_latest(), CONTENT_TYPE_LATEST
