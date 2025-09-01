FROM python:3.11-slim AS builder

WORKDIR /build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY frontend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt gunicorn

FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="autonmap-api frontend" \
      org.opencontainers.image.description="Flask admin panel for autonmap-api" \
      org.opencontainers.image.source="https://github.com/alexzerabr/autonmap-api"

RUN useradd --create-home --shell /usr/sbin/nologin appuser

COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /home/appuser

COPY ./frontend ./

RUN chown -R appuser:appuser /home/appuser

USER appuser

EXPOSE 5000

CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "app:app"]
