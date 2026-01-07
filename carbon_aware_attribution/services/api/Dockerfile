FROM python:3.11

RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    librdkafka-dev \
    libpq-dev \
    openjdk-21-jre \
    libblas-dev \
    liblapack-dev \
    gfortran \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir -e .


# Install ECOS first, then cvxpy[ecos], then all other dependencies for batch/model training
RUN pip install --no-cache-dir ecos
RUN pip install --no-cache-dir cvxpy[ecos]
RUN pip install --no-cache-dir pyspark pandas joblib pyarrow
RUN pip install --no-cache-dir pydantic
RUN pip install --no-cache-dir pydantic-settings

COPY services/api/app /app/app
ENV PYTHONPATH=/app
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]