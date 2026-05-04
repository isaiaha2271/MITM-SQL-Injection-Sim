# MITM-SQL-Injection-Sim

## Overview

This project simulates a combined Man-in-the-Middle (MITM) and SQL Injection attack in a controlled Docker lab environment. The system demonstrates how an attacker positioned between a victim and a vulnerable web application can intercept HTTP traffic, capture login credentials, modify requests, and trigger SQL injection behavior against a backend MySQL database.

The project is designed for reproducibility. A full demo run starts the Docker lab, routes victim traffic through the attacker-controlled `mitmproxy`, sends test requests to vulnerable endpoints, records security events, and generates final metrics and artifacts.

## Architecture

The system consists of four main Docker services:

- `victim`: Simulates a user/client sending HTTP requests.
- `attacker`: Runs `mitmproxy` with a custom addon that observes and modifies traffic.
- `web`: Runs the vulnerable Flask web application.
- `db`: Runs a MySQL database seeded with lab data from `init.sql`.

Traffic follows this path:

```text
victim -> attacker / mitmproxy -> web -> db
```

The victim sends requests through the attacker proxy. The proxy logs credential-bearing requests, injects SQL payloads into selected endpoints, forwards the modified traffic to the web application, and records results as structured artifacts.

## Vulnerable Endpoints Tested

The demo tests multiple vulnerable endpoints, including:

- `/login`
  - Credential interception
  - Optional authentication-bypass SQL injection test

- `/update_company`
  - SQL injection for database modification

- `/find_company_drivers/<company>`
  - SQL injection through a path parameter
  - Data exfiltration and database-modification tests

- `/search`
  - SQL injection through POST form parameters
  - Data exfiltration and final destructive modification test

## Goals

- Demonstrate MITM credential interception over HTTP.
- Show how request parameters can be modified in transit.
- Execute SQL injection payloads against vulnerable Flask endpoints.
- Measure credential interception rate.
- Measure SQL injection success rate.
- Determine whether the full attack chain completed.
- Generate reproducible artifacts for the final report and release.

## Reproducibility

The project is intended to support the following workflow:

```sh
make clean
make demo
```



```sh
./scripts/run_demo.sh
```

A clean run rebuilds the lab, waits for MySQL and the web application to become ready, sends victim requests through the proxy, runs the SQL injection test set, and writes artifacts to:

```text
artifacts/release/
```

## Generated Artifacts

Each demo run generates evidence files in `artifacts/release/`:

- `flows.jsonl`
  - Structured HTTP flow records captured by the proxy addon.

- `security_events.jsonl`
  - Credential capture events and SQL injection attempt records.

- `security_metrics.json`
  - Final calculated metrics such as credential interception rate, SQL injection success rate, and attack chain completion.

- `summary.json`
  - High-level flow and status-code summary.

- `logs.txt`
  - Main demo execution log.

- `attacker.log`
  - Logs from the attacker / `mitmproxy` container.

- `web.log`
  - Logs from the vulnerable Flask web application container.

## Metrics Collected

The final demo measures:

- Credential interception rate
- SQL injection success rate
- Per-endpoint SQL injection success/failure counts
- HTTP status-code distribution
- Attack chain completion

The attack chain is considered complete when at least one credential capture and at least one SQL injection attempt succeed in the same demo run.

## Data Flow

```text
victim
  | HTTP request
  v
attacker / mitmproxy
  | logs and optionally modifies request
  v
web Flask application
  | SQL query
  v
MySQL database
  | response
  v
web Flask application
  |
  v
attacker / mitmproxy
  | logs response and metrics
  v
victim
```

The proxy addon writes structured flow and security data during the run. The metric scripts then summarize this data into final JSON artifacts.

## Notes

This project is intentionally vulnerable and should only be run in the provided Docker lab environment. It is designed for educational demonstration, reproducibility testing, and final project reporting.