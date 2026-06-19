# API image. Torch makes this large, so we install CPU wheels and copy only
# what the service needs at runtime.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install CPU-only torch first from its dedicated index, then the rest.
# Quote the version specifiers so the shell does not treat ">=" as redirection.
RUN pip install --index-url https://download.pytorch.org/whl/cpu \
        "torch>=2.0" "torchvision>=0.15"
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY inspector ./inspector
COPY migrations ./migrations
COPY alembic.ini .

EXPOSE 8000

# Drop privileges. Give appuser ownership of /app so the model cache directory
# can be created and the weights downloaded at startup.
RUN useradd --create-home appuser \
    && mkdir -p /app/.cache \
    && chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "inspector.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
