from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import DateTime, Float, String, Text, create_engine, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )
    source: Mapped[str] = mapped_column(String(32))  # "api" | "batch-pipeline" | ...
    image_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    label: Mapped[str] = mapped_column(String(64), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    is_defect: Mapped[bool] = mapped_column()
    report: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_backend: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[float] = mapped_column(Float)


def create_engine_and_session(database_url: str):
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    engine = create_engine(database_url, connect_args=connect_args, future=True)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return engine, session_factory


class InspectionRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, **fields) -> Inspection:
        record = Inspection(**fields)
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def get(self, inspection_id: int) -> Optional[Inspection]:
        return self._session.get(Inspection, inspection_id)

    def list(self, limit: int = 50, offset: int = 0) -> List[Inspection]:
        stmt = (
            select(Inspection)
            .order_by(Inspection.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(stmt))
