FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -e .

COPY . .

EXPOSE 5001

CMD ["python", "run.py"]