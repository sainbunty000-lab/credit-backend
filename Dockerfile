FROM python:3.10-slim

# ===============================
# Environment Variables
# ===============================
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# ===============================
# Install System Dependencies
# ===============================
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    ghostscript \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ===============================
# Create App User (Security)
# ===============================
RUN useradd -m appuser

# ===============================
# Set Working Directory
# ===============================
WORKDIR /app

# ===============================
# Install Python Dependencies
# ===============================
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# ===============================
# Copy Application Code
# ===============================
COPY . .

# ===============================
# Change Ownership
# ===============================
RUN chown -R appuser:appuser /app

USER appuser

# ===============================
# Healthcheck
# ===============================
HEALTHCHECK --interval=30s --timeout=5s \
 CMD curl -f http://localhost:${PORT:-8000}/docs || exit 1

# ===============================
# Run FastAPI (Production Mode)
# ===============================
CMD ["sh", "-c", "gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000} --workers 2"]
