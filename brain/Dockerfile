FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY brain ./brain

RUN git config --global user.email "brain@el80.space" \
 && git config --global user.name "brain-agent" \
 && git config --global init.defaultBranch main \
 && git config --global --add safe.directory /data/vault

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8765/health || exit 1

CMD ["uvicorn", "brain.main:app", "--host", "0.0.0.0", "--port", "8765"]
