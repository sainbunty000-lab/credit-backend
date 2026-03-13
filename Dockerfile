FROM python:3.10-slim

# =================================
# ENVIRONMENT SETTINGS
# =================================
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

# =================================
# SYSTEM DEPENDENCIES
# =================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    poppler-utils \
    ghostscript \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-osd \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# =================================
# CREATE NON ROOT USER
# =================================
RUN useradd -m appuser

# =================================
# WORKDIR
# =================================
WORKDIR /app

# =================================
# INSTALL PYTHON PACKAGES
# =================================
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# =================================
# COPY PROJECT
# =================================
COPY . .

RUN chown -R appuser:appuser /app
USER appuser

# =================================
# EXPOSE PORT
# Cloud Run injects PORT env var (default 8080).
# EXPOSE is documentation only – actual binding is in CMD.
# =================================
EXPOSE 8080

# =================================
# HEALTH CHECK
# =================================
HEALTHCHECK --interval=30s --timeout=5s \
 CMD curl -f http://localhost:${PORT}/health || exit 1

# =================================
# START FASTAPI
# Uses gunicorn with uvicorn workers.
# Workers set to 1 for Cloud Run (scale via instances).
# =================================
CMD ["sh", "-c", "gunicorn main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT} --workers 1 --timeout 120"]

