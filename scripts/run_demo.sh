#!/bin/sh
set -e


SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

mkdir -p "$REPO_ROOT/artifacts/release"  #ensure artifact folder exists
rm -f "$REPO_ROOT/artifacts/release/flows.jsonl" "$REPO_ROOT/artifacts/release/summary.json"  #clears old logs if they exist


docker compose up -d #build docker containers


#force victims traffic to be routed to attacker (essentially creating MITM path)
docker compose exec victim sh -c "ip route replace default via 172.28.0.10"

#generate some random traffic from the victimm

for url in \
  "http://example.com" \
  "http://neverssl.com" \
  "http://httpbin.org/get" \
  "http://info.cern.ch"\
  "http://eitc.org"

do
  docker compose exec victim sh -c "curl -s '$url' > /dev/null" || true
done

sleep 2

python3 "$REPO_ROOT/scripts/export_summary.py" #create summary artifact



echo "Artifacts written to $REPO_ROOT/artifacts/release"
ls -l "$REPO_ROOT/artifacts/release"