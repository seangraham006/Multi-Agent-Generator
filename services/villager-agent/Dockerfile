FROM python:3.11-slim

WORKDIR /service

# Install dependencies first for layer caching
COPY services/villager-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared/ /service/shared/

# Copy application code
COPY services/villager-agent/app/ /service/app/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/service

CMD ["python", "-m", "app.main"]
