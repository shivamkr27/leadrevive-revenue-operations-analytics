FROM node:22-alpine AS ui
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ backend/
COPY scripts/ scripts/
COPY alembic.ini ./
COPY automation/n8n/workflows/ automation/n8n/workflows/
COPY analytics/sql/ analytics/sql/
COPY --from=ui /build/dist/ frontend/dist/
RUN useradd --create-home appuser && mkdir -p /app/data/processed /app/data/synthetic && chown -R appuser:appuser /app
USER appuser
CMD ["python", "-m", "uvicorn", "backend.app.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
