.PHONY: install dev lint test run frontend batch migrate compose

install:
	pip install -e ".[dev]"

# Full local runtime including the CV and LLM backends.
dev:
	pip install -e ".[dev,cv,llm,gcs,postgres]"

lint:
	ruff check .

test:
	pytest

run:
	uvicorn inspector.api:app --reload --port 8000

frontend:
	INSPECTOR_API_URL=http://localhost:8000 streamlit run frontend/streamlit_app.py

batch:
	inspector-batch --verbose

migrate:
	alembic upgrade head

compose:
	docker compose up --build
