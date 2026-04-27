import sys, json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.export_summary import build_summary, export_summary, load_records


#beta test test that file writes to proper export bath
def test_happy_path_export_summary(tmp_path):
    input_file = tmp_path / "flows.jsonl"
    output_file = tmp_path / "summary.json"

    input_file.write_text(
        '{"timestamp":"t1","method":"GET","url":"http://example.com","host":"example.com","path":"/","status_code":200}\n',
        encoding="utf-8",
    )

    summary = export_summary(input_file, output_file)

    assert output_file.exists()

    saved = json.loads(output_file.read_text(encoding="utf-8"))
    assert saved["total_flows"] == 1
    assert "example.com" in saved["unique_hosts"]
    assert saved["host_counts"]["example.com"] == 1
    assert saved["status_counts"]["200"] == 1
    assert summary == saved

# Alpha negative test and Beta robustness for testing that no records are written to ouput file if no recrods are stored in input file
def test_empty_input_creates_zero_summary(tmp_path):
    input_file = tmp_path / "flows.jsonl"
    output_file = tmp_path / "summary.json"

    summary = export_summary(input_file, output_file)

    assert output_file.exists()
    assert summary["total_flows"] == 0
    assert summary["unique_hosts"] == []
    assert summary["host_counts"] == {}
    assert summary["status_counts"] == {}

#Beta edge case, test for duplicate records(duplicate records should be stored)
def test_duplicate_hosts_counted_correctly():
    records = [
        {"host": "example.com", "status_code": 200},
        {"host": "example.com", "status_code": 200},
        {"host": "neverssl.com", "status_code": 404},
    ]

    summary = build_summary(records)

    assert summary["total_flows"] == 3
    assert summary["host_counts"]["example.com"] == 2
    assert summary["host_counts"]["neverssl.com"] == 1
    assert summary["status_counts"]["200"] == 2
    assert summary["status_counts"]["404"] == 1

#Beta edge/negative case for verifying that code does not crash if status code of a recrod is missing
def test_missing_status_code_does_not_crash():
    records = [
        {"host": "example.com"},
        {"host": "neverssl.com", "status_code": 200},
    ]

    summary = build_summary(records)

    assert summary["total_flows"] == 2
    assert summary["host_counts"]["example.com"] == 1
    assert summary["host_counts"]["neverssl.com"] == 1
    assert summary["status_counts"]["200"] == 1