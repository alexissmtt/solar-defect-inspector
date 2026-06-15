# Solar Inspector

A visual quality-inspection service: it classifies the condition of a solar
panel from a photo and generates a maintenance report, exposed as a deployable
HTTP API with a persistent record of every inspection.

The computer-vision model is demonstrated on solar panels, but the architecture
is domain-agnostic — the same pipeline (classify an image, attach a report,
store and serve the result) applies to defect inspection of any manufactured
product.

The model itself reaches **94.7% test accuracy** (ResNet-50 fine-tuned in two
stages on 1,574 labelled images). This repository is about everything around the
model: turning a notebook prototype into a service you can run, test, deploy and
monitor.

## Live demo

Deployed on **Google Cloud Run**:
**https://solar-inspector-573581836600.europe-west1.run.app**
— interactive API docs at
[`/docs`](https://solar-inspector-573581836600.europe-west1.run.app/docs).

> The service runs the fine-tuned model and scales to zero, so the first request
> after an idle period takes a few seconds to warm up.

## Architecture

The inspection logic does not depend on how it is delivered. A single core is
driven by three thin adapters:

```
            ┌──────────────── core (no web, no UI) ─────────────────┐
            │  classifier ──► reporter ──► repository (PostgreSQL)   │
            └───────────────────────────────────────────────────────┘
                  ▲                  ▲                    ▲
       ┌──────────┴────────┐ ┌───────┴───────┐  ┌─────────┴─────────┐
       │  FastAPI (/inspect)│ │ batch pipeline │  │ Streamlit (client)│
       │  real-time         │ │ folder / GCS   │  │ calls the API     │
       └────────────────────┘ └────────────────┘  └───────────────────┘
```

- **`classifier`** — `ResNetClassifier` (the fine-tuned model) or a deterministic
  `StubClassifier`. Both implement one interface, so the rest of the system runs
  and is tested without torch installed.
- **`reporter`** — `GroqReporter` (Llama 3.3 70B) or a rule-based
  `TemplateReporter` used as a test double and as a fallback when no LLM key is
  set.
- **`service`** — the use case: classify → report (only if a defect) → persist →
  emit metrics. Used identically by the API and the batch pipeline.
- **`db`** — SQLAlchemy 2.0 model + repository; schema managed with Alembic.

## Quickstart

Runs with zero configuration (SQLite + stub classifier + template reporter):

```bash
pip install -e ".[dev]"
make run          # API on http://localhost:8000/docs
```

```bash
curl -F "file=@panel.jpg" http://localhost:8000/inspect
```

To run the real model and LLM, install the extras and switch backends:

```bash
pip install -e ".[dev,cv,llm]"
INSPECTOR_CLASSIFIER_BACKEND=torch INSPECTOR_REPORTER_BACKEND=groq \
  INSPECTOR_GROQ_API_KEY=gsk_... make run
```

## Full stack with Docker

`docker compose up --build` starts PostgreSQL, the API and the Streamlit UI, runs
the Alembic migration on boot, and wires them together:

- API + docs: http://localhost:8000/docs
- UI: http://localhost:8501

## API

| Method | Path                  | Purpose                                  |
|--------|-----------------------|------------------------------------------|
| GET    | `/health`             | Liveness and active backends             |
| POST   | `/inspect`            | Classify one uploaded image, store, return |
| GET    | `/inspections`        | Recent inspection history                |
| GET    | `/inspections/{id}`   | A single inspection                      |
| GET    | `/metrics`            | Prometheus metrics                       |

## Batch ingestion

`inspector-batch` runs the same inspection over a whole batch of images from a
local folder or a GCS bucket, writing the results to the database — the path you
would schedule as a CronJob for nightly factory uploads.

```bash
INSPECTOR_STORAGE_ROOT=./data/incoming inspector-batch --verbose
```

## Tests

```bash
ruff check . && pytest
```

The suite covers the classifier, reporter, service, API (via `TestClient`) and
the batch pipeline. It runs against SQLite and the stub backends, so it needs no
GPU, no model download and no API key — which is what keeps CI fast (see
`.github/workflows/ci.yml`).

## Deployment

Container image plus a Postgres database; runs on Cloud Run or GKE. See
[`deploy/README.md`](deploy/README.md).

## Stack

Python · FastAPI · PyTorch (ResNet-50) · Llama 3.3 70B (Groq) · SQLAlchemy ·
Alembic · PostgreSQL · Prometheus · Docker · Kubernetes · Google Cloud · pytest ·
GitHub Actions.
