FROM python:3.11-slim

ENV PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first for caching
COPY appointment_app/requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn

# Copy full project
COPY . .

# Expose the API port
EXPOSE 5000

# Default command (overridden by docker-compose)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "appointment_app.app:app"]
