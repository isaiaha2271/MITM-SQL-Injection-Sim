import json
from datetime import datetime
from mitmproxy import http

LOG_FILE = "/artifacts/flows.jsonl"

def response(flow: http.HTTPFlow) -> None:
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "method": flow.request.method,
        "url": flow.request.pretty_url,
        "host": flow.request.host,
        "path": flow.request.path,
        "status_code": flow.response.status_code if flow.response else None,
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")