FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    librdkafka-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml

RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -e .

COPY services/stream_processor/app /app/app

CMD ["python", "-m", "app.main"]