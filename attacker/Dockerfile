FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    iptables \
    iproute2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install mitmproxy

WORKDIR /app

COPY start.sh /app/start.sh
COPY addon.py /app/addon.py

RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]