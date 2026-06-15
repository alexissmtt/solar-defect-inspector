FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY frontend/requirements.txt .
RUN pip install -r requirements.txt

COPY frontend/streamlit_app.py .

EXPOSE 8501
# Flags needed to run behind the Cloud Run HTTPS proxy.
CMD ["streamlit", "run", "streamlit_app.py", \
     "--server.address=0.0.0.0", "--server.port=8501", \
     "--server.headless=true", "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false", "--browser.gatherUsageStats=false"]
