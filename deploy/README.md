# Deployment

The service is a stateless container plus a Postgres database, so it runs the
same way on any container platform. Below is the path on Google Cloud (the
target stack), with both a serverless and a Kubernetes option.

## 1. Build and push the image

```bash
# Artifact Registry
gcloud auth configure-docker europe-west1-docker.pkg.dev
docker build -t europe-west1-docker.pkg.dev/PROJECT_ID/inspector/api:latest .
docker push europe-west1-docker.pkg.dev/PROJECT_ID/inspector/api:latest
```

## 2a. Cloud Run (serverless, simplest)

```bash
gcloud run deploy inspector-api \
  --image europe-west1-docker.pkg.dev/PROJECT_ID/inspector/api:latest \
  --region europe-west1 \
  --add-cloudsql-instances PROJECT_ID:europe-west1:inspector-db \
  --set-env-vars INSPECTOR_CLASSIFIER_BACKEND=torch,INSPECTOR_AUTO_CREATE_TABLES=false \
  --set-secrets INSPECTOR_DATABASE_URL=inspector-db-url:latest,INSPECTOR_GROQ_API_KEY=groq-key:latest \
  --allow-unauthenticated
```

The database is a Cloud SQL for PostgreSQL instance; the batch pipeline reads
images from a Cloud Storage bucket (`INSPECTOR_STORAGE_BACKEND=gcs`).

## 2b. GKE (Kubernetes)

```bash
kubectl apply -f deploy/k8s/configmap.yaml
kubectl create secret generic inspector-secrets \
  --from-literal=INSPECTOR_DATABASE_URL='postgresql+psycopg://...' \
  --from-literal=INSPECTOR_GROQ_API_KEY='gsk_...'
kubectl apply -f deploy/k8s/deployment.yaml
kubectl apply -f deploy/k8s/service.yaml
```

The deployment runs `alembic upgrade head` in an init container before the API
starts, and exposes `/health` for readiness and liveness probes.

## Batch pipeline as a scheduled job

The ingestion pipeline (`inspector-batch`) is a one-shot process, so on
Kubernetes it fits a `CronJob` (e.g. hourly) pointed at the GCS bucket; on Cloud
Run it fits a Cloud Run Job triggered by Cloud Scheduler.
