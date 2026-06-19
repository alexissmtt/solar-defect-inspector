from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class InspectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    created_at: datetime
    source: str
    image_name: Optional[str]
    label: str
    confidence: float
    is_defect: bool
    report: Optional[str]
    model_backend: str
    latency_ms: float


class HealthOut(BaseModel):
    status: str
    classifier_backend: str
    reporter_backend: str
    version: str
