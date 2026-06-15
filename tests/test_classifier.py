from __future__ import annotations

from PIL import Image

from inspector.classifier import DEFAULT_CLASSES, Prediction, StubClassifier


def test_prediction_is_defect_flag():
    assert Prediction("Clean", 99.0, {}).is_defect is False
    assert Prediction("Dusty", 80.0, {}).is_defect is True


def test_stub_returns_valid_prediction():
    clf = StubClassifier()
    pred = clf.predict(Image.new("RGB", (32, 32), (10, 20, 30)))

    assert pred.label in DEFAULT_CLASSES
    assert 0 <= pred.confidence <= 100
    assert set(pred.probabilities) == set(DEFAULT_CLASSES)
    assert abs(sum(pred.probabilities.values()) - 100.0) < 1e-6
    # the reported confidence is the top class probability
    assert pred.probabilities[pred.label] == pred.confidence


def test_stub_is_deterministic():
    clf = StubClassifier()
    image = Image.new("RGB", (32, 32), (200, 100, 50))
    assert clf.predict(image).label == clf.predict(image).label


def test_stub_distinguishes_different_images():
    clf = StubClassifier()
    labels = {
        clf.predict(Image.new("RGB", (32, 32), (i * 11 % 255, i, 0))).label
        for i in range(40)
    }
    # different inputs should not all collapse to a single class
    assert len(labels) > 1
