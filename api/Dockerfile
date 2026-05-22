# Backend image: FastAPI + the in-house ML stack.
#
# Two stages:
#   1. ``deps``  installs the small Python wheel set
#   2. ``run``   copies the app and trains lazily on first request
#
# At runtime the API picks a storage backend automatically: if Mongo
# is reachable it uses it, otherwise it falls back to the in-memory
# store that loads FAQs from data/faqs.jsonl.

FROM python:3.12-slim AS deps

WORKDIR /opt/app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System wheels for numpy / scipy build paths.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt /opt/app/requirements.txt
RUN pip install --no-cache-dir -r /opt/app/requirements.txt

# -------------------------------------------------------------------
FROM python:3.12-slim AS run

WORKDIR /opt/app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/opt/app/api

COPY --from=deps /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy the source tree.
COPY api /opt/app/api
COPY data /opt/app/data

EXPOSE 8000

WORKDIR /opt/app/api

# Healthcheck so docker compose can wait properly.
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=4 \
    CMD python -c "import urllib.request,sys; \
                   sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
