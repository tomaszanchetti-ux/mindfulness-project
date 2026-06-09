# Backend Dwellia (FastAPI) para Cloud Run.
# Contexto de build = raíz del repo, para incluir el contenido global de M0
# (el seed lo lee desde la raíz: M0_Motor_de_Contenido/data).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 1) Dependencias (capa cacheable)
COPY apps/api/requirements.txt /app/apps/api/requirements.txt
RUN pip install -U pip && pip install -r /app/apps/api/requirements.txt

# 2) Código del backend + contenido global M0 (preserva el layout que espera el seed)
COPY apps/api /app/apps/api
COPY M0_Motor_de_Contenido/data /app/M0_Motor_de_Contenido/data

WORKDIR /app/apps/api

# Cloud Run inyecta PORT (8080 por defecto).
ENV PORT=8080
CMD ["sh", "-c", "uvicorn mindful_api.main:app --host 0.0.0.0 --port ${PORT}"]
