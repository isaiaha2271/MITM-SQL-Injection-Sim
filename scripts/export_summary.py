import json
from collections import Counter
from pathlib import Path


def load_records(input_file: Path) -> list[dict]:
    records = []
    if input_file.exists():
        with input_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
    return records


def build_summary(records: list[dict]) -> dict:
    host_counts = Counter(r["host"] for r in records if r.get("host"))
    status_counts = Counter(
        str(r["status_code"])
        for r in records
        if r.get("status_code") is not None
    )

    return {
        "total_flows": len(records),
        "unique_hosts": sorted(host_counts.keys()),
        "host_counts": dict(host_counts),
        "status_counts": dict(status_counts),
    }


def export_summary(input_file: Path, output_file: Path) -> dict:
    records = load_records(input_file)
    summary = build_summary(records)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent
    input_file = repo_root / "artifacts" / "release" / "flows.jsonl"
    output_file = repo_root / "artifacts" / "release" / "summary.json"

    summary = export_summary(input_file, output_file)
    print(json.dumps(summary, indent=2))