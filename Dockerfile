FROM python:3.10-slim

# Zainstaluj zależności systemowe dla PyMuPDF i EasyOCR
RUN apt-get update && apt-get install -y \
    libmupdf-dev \
    mupdf-tools \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Zainstaluj zależności Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Skopiuj kod aplikacji
COPY rag/ ./rag/
COPY scripts/ ./scripts/

# Utwórz katalogi dla wolumenów
RUN mkdir -p /app/input /app/output /app/data

# Utwórz użytkownika non-root (UID dopasowany do hosta)
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN groupadd -g ${GROUP_ID} appuser && \
    useradd -m -u ${USER_ID} -g ${GROUP_ID} appuser && \
    chown -R appuser:appuser /app
USER appuser

# Domyślne polecenie (może być nadpisane)
CMD ["python", "scripts/ask.py"]
