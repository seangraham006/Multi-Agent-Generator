FROM python:3.11-slim

WORKDIR /service

# Install build deps for psycopg2 and sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first for layer caching
COPY services/memory-controller/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared/ /service/shared/

# Copy application code
COPY services/memory-controller/app/ /service/app/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/service

CMD ["python", "-m", "app.main"]
