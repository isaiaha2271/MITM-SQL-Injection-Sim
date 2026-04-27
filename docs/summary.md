# What Works / What’s Next

## What Works

- Transparent MITM interception of HTTP traffic
- Victim traffic successfully routed through attacker container
- Requests captured and logged using mitmproxy
- Structured logs exported to JSON (flows.jsonl)
- Summary metrics generated (summary.json)
- Automated demo via make up && make demo
- Unit tests implemented with coverage
- WebApp endpoints (login, registration, logout,  dashboard, search, update_phone_number, lookup)
     - SQL Injection vulnerable endpoints: login, dashboard, search, lookup
- Basic user authentication on webapp
   

## What’s Next

- Integrate MITM pipeline with sql injection vulnerable web application
- Capture victim request payloads (credentials, payload data) and log it
- Attacker use intercepted credentials to access victim data in DB
- Attacker perform SQL injection attacks to bypass webapp authetnication, access and modify database 
- Capture and analyze SQL injection traffic 
- Improve logging to preserve domain names instead of IPs
