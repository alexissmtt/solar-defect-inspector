"""FastAPI application: the real-time delivery mechanism.

Endpoints:
    GET  /health            liveness + which backends are active
    POST /inspect           classify one uploaded image, store and return it
    GET  /inspections       recent inspection history
    GET  /inspections/{id}  one inspection
    GET  /metrics           Prometheus metrics

The classifier and reporter are built once at startup (they are read-only and
safe to share); a fresh database session is created per request.
"""

from __future__ import annotations

import io
from typing import List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import RedirectResponse
from PIL import Image, UnidentifiedImageError

from . import __version__, metrics
from .classifier import build_classifier
from .config import Settings, get_settings
from .db import Base, InspectionRepository, create_engine_and_session
from .reporter import build_reporter
from .schemas import HealthOut, InspectionOut
from .service import InspectionService


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    settings = settings or get_settings()

    engine, session_factory = create_engine_and_session(settings.database_url)
    if settings.auto_create_tables:
        Base.metadata.create_all(engine)

    # Shared, read-only collaborators built once.
    classifier = build_classifier(settings)
    reporter = build_reporter(settings)

    app = FastAPI(title="Solar Inspector", version=__version__)

    def get_session():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    def get_service(session=Depends(get_session)) -> InspectionService:
        return InspectionService(
            classifier=classifier,
            reporter=reporter,
            repository=InspectionRepository(session),
            model_backend=settings.classifier_backend,
        )

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        # Land on the interactive API docs when the base URL is opened.
        return RedirectResponse(url="/docs")

    @app.get("/health", response_model=HealthOut)
    def health() -> HealthOut:
        return HealthOut(
            status="ok",
            classifier_backend=settings.classifier_backend,
            reporter_backend=settings.reporter_backend,
            version=__version__,
        )

    @app.post("/inspect", response_model=InspectionOut)
    async def inspect(
        file: UploadFile = File(...),
        service: InspectionService = Depends(get_service),
    ) -> InspectionOut:
        raw = await file.read()
        if len(raw) > settings.max_upload_bytes:
            raise HTTPException(status_code=413, detail="Uploaded image is too large")
        try:
            image = Image.open(io.BytesIO(raw)).convert("RGB")
        except (UnidentifiedImageError, Image.DecompressionBombError):
            raise HTTPException(
                status_code=400, detail="Uploaded file is not a valid image"
            ) from None
        # Inference is CPU-bound and synchronous; run it off the event loop so a
        # slow prediction does not block other requests.
        record = await run_in_threadpool(service.inspect, image, "api", file.filename)
        return InspectionOut.model_validate(record)

    @app.get("/inspections", response_model=List[InspectionOut])
    def list_inspections(
        limit: int = 50,
        offset: int = 0,
        session=Depends(get_session),
    ) -> List[InspectionOut]:
        records = InspectionRepository(session).list(limit=limit, offset=offset)
        return [InspectionOut.model_validate(r) for r in records]

    @app.get("/inspections/{inspection_id}", response_model=InspectionOut)
    def get_inspection(inspection_id: int, session=Depends(get_session)) -> InspectionOut:
        record = InspectionRepository(session).get(inspection_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Inspection not found")
        return InspectionOut.model_validate(record)

    @app.get("/metrics")
    def prometheus_metrics() -> Response:
        payload, content_type = metrics.render()
        return Response(content=payload, media_type=content_type)

    return app


app = create_app()
