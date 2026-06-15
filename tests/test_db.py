from __future__ import annotations

from sqlalchemy import inspect as sa_inspect

from inspector.db import Base, create_engine_and_session


def test_model_declares_indexes(tmp_path):
    # The ORM model must declare the same indexes the Alembic migration creates,
    # so auto-created (dev) and migrated (prod) schemas match.
    engine, _ = create_engine_and_session(f"sqlite:///{tmp_path / 'idx.db'}")
    Base.metadata.create_all(engine)

    indexed = {
        tuple(ix["column_names"])
        for ix in sa_inspect(engine).get_indexes("inspections")
    }
    assert ("created_at",) in indexed
    assert ("label",) in indexed
