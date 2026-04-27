#!/bin/sh
set -e


mkdir -p artifacts/release   #ensure artifact folder exists
rm -f artifacts/release/flows.jsonl artifacts/release/summary.json #clears old logs if they exist

docker compose up -d #build docker containers


#force victims traffic to be routed to attacker (essentially creating MITM path)
docker compose exec victim sh -c "ip route del default || true"
docker compose exec victim sh -c "ip route replace default via 172.28.0.10"

#generate some random traffic
docker compose exec victim sh -c "curl -s http://example.com > /dev/null"
docker compose exec victim sh -c "curl -s http://neverssl.com > /dev/null"
docker compose exec victim sh -c "curl -s http://lebronisnotthegoat.com > /dev/null"
docker compose exec victim sh -c "curl -s http://seancoreycarter.com > /dev/null"
docker compose exec victim sh -c "curl -s http://nasirjones.com > /dev/null"
docker compose exec victim sh -c "curl -s http://canbushacks.com > /dev/null"



sleep 2

python3 scripts/export_summary.py #creates summary artificat

echo "Artifacts written to artifacts/release/"
ls -l artifacts/release/