FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential nmap && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml ./
COPY api ./api
RUN pip install --no-cache-dir .

FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="autonmap-api backend" \
      org.opencontainers.image.description="FastAPI backend for autonmap-api" \
      org.opencontainers.image.source="https://github.com/alexzerabr/autonmap-api"

RUN useradd --create-home --shell /usr/sbin/nologin appuser

RUN apt-get update && \
    apt-get install -y --no-install-recommends nmap procps redis-tools && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /home/appuser

COPY ./api ./api
COPY ./scripts ./scripts
RUN chown -R appuser:appuser /home/appuser

USER appuser

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]