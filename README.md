# Solar Inspector

[![Live demo](https://img.shields.io/badge/▶_Live_demo-Google_Cloud_Run-4285F4?logo=googlecloud&logoColor=white)](https://solar-inspector-ui-573581836600.europe-west1.run.app)
[![CI](https://github.com/alexissmtt/solar-defect-inspector/actions/workflows/ci.yml/badge.svg)](https://github.com/alexissmtt/solar-defect-inspector/actions)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)

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

## Live demo — deployed on Google Cloud Run

**▶️ Try the web app:** https://solar-inspector-ui-573581836600.europe-west1.run.app

Upload a panel photo and get the defect class, a confidence score and an
auto-generated maintenance report.

> Both scale to zero, so the first request after an idle period takes a few
> seconds to warm up.

## The model

A **ResNet-50** fine-tuned to classify the condition of a solar panel into six
classes:

| Class | Meaning |
|-------|---------|
| Clean | healthy panel |
| Dusty | dust accumulation |
| Bird-drop | bird droppings |
| Snow-Covered | partial or full snow cover |
| Electrical-damage | hot spots, delamination, electrical faults |
| Physical-Damage | cracks, broken glass, mechanical damage |

**Approach** — transfer learning on ResNet-50 (pre-trained on ImageNet),
fine-tuned in **two stages**: first the classifier head, then `layer4` unfrozen
with a lower learning rate. Trained on **1,574 labelled images** (Kaggle PV panel
defect dataset) on a Colab T4 GPU.

| Metric | Score |
|--------|-------|
| Validation accuracy | 97.3% |
| Test accuracy | **94.7%** |
| Inference | < 2 s |

When a defect is detected, the prediction is turned into a maintenance report —
severity, recommended action and estimated production loss — by the Groq / Llama
3.3 70B reporter, or a rule-based template when no LLM key is set.

## Architecture

The inspection logic does not depend on how it is delivered. A single core is
driven by three thin adapters:

```
            ┌──────────────── core (no web, no UI) ─────────────────┐
            │  classifier ──► reporter ──► repository (database)     │
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

## Configuration

Every part is selected through environment variables, so it can be swapped
without touching code. The columns below also describe what the live demo runs.

| Concern    | Live demo (default)        | Other option                                     |
|------------|----------------------------|--------------------------------------------------|
| Classifier | fine-tuned ResNet-50       | deterministic stub (used by the test suite)      |
| Reporter   | rule-based template        | Groq / Llama 3.3 70B (`INSPECTOR_GROQ_API_KEY`)  |
| Store      | embedded SQLite            | PostgreSQL (used by `docker-compose`)            |

## API

A separate Cloud Run service, with interactive OpenAPI docs for developers at
[`/docs`](https://solar-inspector-573581836600.europe-west1.run.app/docs).

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

Live on **Google Cloud Run** — two services, the API and the Streamlit UI (see
the links at the top). The same container also runs on Kubernetes; manifests are
in [`deploy/`](deploy/README.md).

## Stack

Python · FastAPI · PyTorch (ResNet-50) · Llama 3.3 70B (Groq) · SQLAlchemy ·
Alembic · PostgreSQL · Prometheus · Docker · Kubernetes · Google Cloud · pytest ·
GitHub Actions.
