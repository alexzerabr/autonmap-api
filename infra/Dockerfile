# Stage 1: Build
FROM python:3.11-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential nmap && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final image
FROM python:3.11-slim as final

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /home/appuser

# Instalar Nmap e dependências de runtime
RUN apt-get update && \
    apt-get install -y --no-install-recommends nmap procps redis-tools && \
    rm -rf /var/lib/apt/lists/*

# Copiar dependências instaladas do builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar código da aplicação
COPY --chown=appuser:appuser ./api /home/appuser/api
COPY --chown=appuser:appuser ./scripts /home/appuser/scripts

# Dar permissão de execução ao script
RUN chmod +x /home/appuser/scripts/autonmap

USER appuser

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
