#!/bin/sh
set -e

mkdir -p /artifacts

mitmdump \
  --mode regular \
  --listen-host 0.0.0.0 \
  --listen-port 8080 \
  --showhost \
  -s /app/addon.py