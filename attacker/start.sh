#!/bin/sh
set -e

mkdir -p /artifacts

iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080

mitmdump \
  --mode transparent \
  --showhost \
  -s /app/addon.py