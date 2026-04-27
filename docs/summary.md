# What Works / What’s Next

## What Works

- Transparent MITM interception of HTTP traffic
- Victim traffic successfully routed through attacker container
- Requests captured and logged using mitmproxy
- Structured logs exported to JSON (flows.jsonl)
- Summary metrics generated (summary.json)
- Automated demo via make up && make demo
- Unit tests implemented with coverage
- 

## What’s Next

- Integrate MITM pipeline with vulnerable web application
- Capture victim request payloads (credentials, payload data) and log it
- Attacker use intercepted credentials to access user data in DB
- Attacker container perform SQL injection to bypass webapp authetnication, access and modify database 
- Capture and analyze SQL injection traffic 
- Improve logging to preserve domain names instead of IPs
