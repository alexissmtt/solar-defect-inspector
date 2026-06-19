from __future__ import annotations

import argparse
import io
import logging
from typing import Dict

from PIL import Image

from .classifier import build_classifier
from .config import Settings, get_settings
from .db import Base, InspectionRepository, create_engine_and_session
from .reporter import build_reporter
from .service import InspectionService
from .storage import ObjectStore, build_store

logger = logging.getLogger("inspector.pipeline")


def run_batch(
    store: ObjectStore, service: InspectionService, source: str = "batch-pipeline"
) -> Dict:
    keys = store.list_keys()
    logger.info("found %d image(s) to process", len(keys))

    processed = 0
    defects = 0
    by_label: Dict[str, int] = {}
    for key in keys:
        try:
            image = Image.open(io.BytesIO(store.read(key))).convert("RGB")
        except Exception as exc:  # noqa: BLE001 - skip unreadable files, keep going
            logger.warning("skipping %s: %s", key, exc)
            continue
        record = service.inspect(image, source=source, image_name=key)
        processed += 1
        defects += int(record.is_defect)
        by_label[record.label] = by_label.get(record.label, 0) + 1
        logger.info("%s -> %s (%.1f%%)", key, record.label, record.confidence)

    return {
        "processed": processed,
        "defects": defects,
        "by_label": by_label,
    }


def build_service(settings: Settings, session) -> InspectionService:
    return InspectionService(
        classifier=build_classifier(settings),
        reporter=build_reporter(settings),
        repository=InspectionRepository(session),
        model_backend=settings.classifier_backend,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the batch inspection pipeline.")
    parser.add_argument("--source-label", default="batch-pipeline")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    settings = get_settings()
    engine, session_factory = create_engine_and_session(settings.database_url)
    if settings.auto_create_tables:
        Base.metadata.create_all(engine)
    store = build_store(settings)
    session = session_factory()
    try:
        service = build_service(settings, session)
        summary = run_batch(store, service, source=args.source_label)
    finally:
        session.close()
    print(
        f"processed={summary['processed']} defects={summary['defects']} "
        f"by_label={summary['by_label']}"
    )


if __name__ == "__main__":
    main()
