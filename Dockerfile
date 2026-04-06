# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

# Métadonnées
LABEL org.opencontainers.image.title="correzeboostemploi-scraper"
LABEL org.opencontainers.image.description="Scraper d'offres CDI/CDD en Corrèze avec notifications Discord"
LABEL org.opencontainers.image.source="https://github.com/aerya/correzeboostemploi"

# Pas de .pyc, logs non bufferisés
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data

# Copie des dépendances depuis le build stage
COPY --from=builder /install /usr/local

WORKDIR /app
COPY scraper.py scheduler.py ./

# Volume pour la persistance des offres déjà vues
VOLUME ["/data"]

# Utilisateur non-root
RUN useradd -r -u 1001 -m scraper && chown -R scraper:scraper /app
USER scraper

CMD ["python", "scheduler.py"]
