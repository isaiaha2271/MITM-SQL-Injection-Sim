FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    curl \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

CMD ["sleep", "infinity"]