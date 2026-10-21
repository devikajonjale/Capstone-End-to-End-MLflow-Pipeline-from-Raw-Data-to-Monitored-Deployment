# Serving image for the house price model. The promoted model and its lineage
# travel with the image (models/production), so the container scores listings
# without needing a running MLflow server.
FROM python:3.11-slim AS base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/
COPY models/ ./models/
COPY datasets/ ./datasets/
COPY run_pipeline.py run_monitoring.py ./
COPY scripts/ ./scripts/

EXPOSE 8000

# Record the commit the image was built from so a running container can be
# traced back to source. Passed in by the release workflow.
ARG GIT_COMMIT=unknown
ENV GIT_COMMIT=${GIT_COMMIT}
LABEL org.opencontainers.image.revision=${GIT_COMMIT}

CMD ["uvicorn", "src.serving.app:app", "--host", "0.0.0.0", "--port", "8000"]
