"""The inspection use-case, independent of any delivery mechanism.

`InspectionService.inspect` is the single entry point used by the API, the batch
pipeline and (indirectly) the frontend. It classifies an image, generates a
report when a defect is found, persists the record and emits metrics.
"""

from __future__ import annotations

import time

from PIL import Image

from . import metrics
from .classifier import Classifier
from .db import Inspection, InspectionRepository
from .reporter import Reporter


class InspectionService:
    def __init__(
        self,
        classifier: Classifier,
        reporter: Reporter,
        repository: InspectionRepository,
        model_backend: str = "stub",
    ):
        self._classifier = classifier
        self._reporter = reporter
        self._repository = repository
        self._model_backend = model_backend

    def inspect(self, image: Image.Image, source: str, image_name: str = None) -> Inspection:
        start = time.perf_counter()
        prediction = self._classifier.predict(image)
        report = self._reporter.generate(prediction) if prediction.is_defect else None
        latency_ms = (time.perf_counter() - start) * 1000

        record = self._repository.add(
            source=source,
            image_name=image_name,
            label=prediction.label,
            confidence=prediction.confidence,
            is_defect=prediction.is_defect,
            report=report,
            model_backend=self._model_backend,
            latency_ms=latency_ms,
        )
        metrics.record(prediction, source=source, latency_ms=latency_ms)
        return record
