import json
from collections import defaultdict
from pathlib import Path

# Input and output artifact paths.
# security_events.jsonl is produced by addon.py.
# security_metrics.json is the final summary of recorded metrics.
EVENTS_PATH = Path("artifacts/release/security_events.jsonl")
OUT_PATH = Path("artifacts/release/security_metrics.json")


def pct(numerator, denominator):
    """
    Safely compute a rate.

    Returns 0.0 if the denominator is zero so the script never crashes
    when no events were recorded.
    """
    if denominator == 0:
        return 0.0

    return round(numerator / denominator, 4)


def main():
    '''Credential interception counters. 
        total_login_requests:
            Number of POST /login requests seen by mitmproxy.

        captured_login_requests:
            Number of login requests where both username and password were readable by mitmproxy.'''
    credential_total = 0
    credential_captured = 0



    '''SQL injection counters.
        sqli_total:
            Number of modified SQLi attempts.
        sqli_success:
            Number of SQLi attempts that met the success rule from addon.py.'''
    
    sqli_total = 0
    sqli_success = 0

    # Endpoint-level breakdown to show which endpoints were easiest/hardest to exploit.
    by_endpoint = defaultdict(lambda: {
        "total": 0,
        "success": 0,
        "fail": 0,
        "status_counts": defaultdict(int),
        "attack_goals": defaultdict(int),
    })

    # Preserve raw security events inside the final JSON summary.
    events = []

    # Read security_events.jsonl if it exists.
    # Each line is one JSON object produced by addon.py.
    if EVENTS_PATH.exists():
        with EVENTS_PATH.open("r", encoding="utf-8") as f:
            for line in f:
                event = json.loads(line)
                events.append(event)

                event_type = event.get("event_type")

                # Credential interception metric.
                if event_type == "credential_capture":
                    credential_total += 1

                    if event.get("captured_credentials"):
                        credential_captured += 1

                # SQL injection success/failure metric.
                elif event_type == "sqli_attempt":
                    sqli_total += 1

                    success = bool(event.get("success"))
                    endpoint = event.get("endpoint", "unknown")
                    status_code = str(event.get("status_code"))
                    attack_goal = event.get("attack_goal", "unknown")

                    if success:
                        sqli_success += 1
                        by_endpoint[endpoint]["success"] += 1
                    else:
                        by_endpoint[endpoint]["fail"] += 1

                    by_endpoint[endpoint]["total"] += 1
                    by_endpoint[endpoint]["status_counts"][status_code] += 1
                    by_endpoint[endpoint]["attack_goals"][attack_goal] += 1

    # Success conditions.
    # Credential interception succeeds if at least one login attempt had
    # readable credentials.

    # SQL injection succeeds if at least one SQLi attempt resulted in successful access, exfiltration, or modification evidence.
    # Attack chain succeeds if both(credential interception and sql injection) happened at least once.
    credential_success_condition = credential_captured >= 1
    sqli_success_condition = sqli_success >= 1
    attack_chain_completed = credential_success_condition and sqli_success_condition

    summary = {
        "credential_interception": {
            "total_login_requests": credential_total,
            "captured_login_requests": credential_captured,
            "credential_interception_rate": pct(credential_captured, credential_total),
            "success_condition_met": credential_success_condition,
        },
        "sql_injection": {
            "total_sqli_attempts": sqli_total,
            "successful_sqli_attempts": sqli_success,
            "failed_sqli_attempts": sqli_total - sqli_success,
            "sql_injection_success_rate": pct(sqli_success, sqli_total),
            "success_condition_met": sqli_success_condition,
            "by_endpoint": {},
        },
        "attack_chain": {
            "credential_capture_success": credential_success_condition,
            "sql_injection_success": sqli_success_condition,
            "attack_chain_completed": attack_chain_completed,
        },
        "events": events,
    }

    # Convert defaultdicts into normal dictionaries so json.dump works cleanly.
    for endpoint, stats in by_endpoint.items():
        summary["sql_injection"]["by_endpoint"][endpoint] = {
            "total": stats["total"],
            "success": stats["success"],
            "fail": stats["fail"],
            "success_rate": pct(stats["success"], stats["total"]),
            "status_counts": dict(stats["status_counts"]),
            "attack_goals": dict(stats["attack_goals"]),
        }

    # Write final report-ready metrics file.
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Also print the summary so make demo / run_demo.sh shows results.
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()