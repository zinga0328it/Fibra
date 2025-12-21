# Dockerfile per FTTH Management System
FROM python:3.11-slim

# Metadata
LABEL maintainer="FTTH Management Team"
LABEL description="Sistema di gestione ordini fibra ottica con architettura distribuita"
LABEL version="1.0"

# Imposta working directory
WORKDIR /app

# Installa dipendenze di sistema
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Crea utente non-root
RUN useradd --create-home --shell /bin/bash ftth

# Copia requirements e installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia codice applicazione
COPY . .

# Crea directory per logs e imposta permessi
RUN mkdir -p logs && \
    chown -R ftth:ftth /app

# Passa all'utente non-root
USER ftth

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:6030/health || exit 1

# Esponi porta
EXPOSE 6030

# Comando di avvio
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "6030", "--workers", "2"]