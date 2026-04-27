import json
from collections import Counter
from pathlib import Path



'''converts raw json logs from attacker into more detailed json logs wiht a few statistics (which hsots t
the victim tries to reach, '''
input_file = Path("artifacts/release/flows.jsonl")
output_file = Path("artifacts/release/summary.json")

records = []

if input_file.exists():
    with input_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

#count number of hsots victim atempted to reach and status codes
host_counts = Counter(r["host"] for r in records if r.get("host"))
status_counts = Counter(str(r["status_code"]) for r in records if r.get("status_code") is not None)

summary = {
    "total_flows": len(records), # represent number of attempted connections attcker sucessuflly intercepted
    "unique_hosts": sorted(host_counts.keys()),
    "host_counts": dict(host_counts),
    "status_counts": dict(status_counts),
}

with output_file.open("w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print(json.dumps(summary, indent=2))