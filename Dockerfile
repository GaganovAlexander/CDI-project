FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    python3-dev \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src /app

WORKDIR /app

CMD ["hypercorn", "--bind", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-", "src.main:app"]
