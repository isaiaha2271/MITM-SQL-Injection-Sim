import json
from datetime import datetime
from urllib.parse import quote

from mitmproxy import http

LOG_FILE = "/artifacts/flows.jsonl"

# Put your tested payloads here.
# Keep them based on seeded init.sql data only.
PAYLOADS = {
    "login_username": "YOUR_LOGIN_USERNAME_PAYLOAD",
    "login_password": "YOUR_LOGIN_PASSWORD_PAYLOAD",

    "search_firstName": "YOUR_SEARCH_FIRSTNAME_PAYLOAD",
    "search_lastName": "YOUR_SEARCH_LASTNAME_PAYLOAD",

    "update_company": "YOUR_UPDATE_COMPANY_PAYLOAD",

    "find_company_drivers": "YOUR_COMPANY_PATH_PAYLOAD",
}


def mark_modified(flow: http.HTTPFlow, endpoint: str, field: str, original: str, modified: str) -> None:
    changes = flow.metadata.setdefault("sqli_changes", [])
    changes.append({
        "endpoint": endpoint,
        "field": field,
        "original": original,
        "modified": modified,
    })
    flow.metadata["sqli_modified"] = True


def replace_form_field(flow: http.HTTPFlow, endpoint: str, field: str, payload_key: str) -> None:
    original = flow.request.urlencoded_form.get(field, "")
    modified = PAYLOADS[payload_key]

    flow.request.urlencoded_form[field] = modified
    mark_modified(flow, endpoint, field, original, modified)


def request(flow: http.HTTPFlow) -> None:
    if flow.request.host != "web":
        return

    method = flow.request.method
    path = flow.request.path

    # POST /login
    # Use  to demo login SQLi.
    #
    # if method == "POST" and path == "/login":
    #     replace_form_field(flow, "/login", "username", "login_username")
    #     replace_form_field(flow, "/login", "password", "login_password")
    #     return

    # POST /search
    if method == "POST" and path == "/search":
        replace_form_field(flow, "/search", "firstName", "search_firstName")
        replace_form_field(flow, "/search", "lastName", "search_lastName")
        return

    # POST /update_company
    if method == "POST" and path == "/update_company":
        replace_form_field(flow, "/update_company", "new_company", "update_company")
        return

    # GET /find_company_drivers/<company>
    if method == "GET" and path.startswith("/find_company_drivers/"):
        original_path = flow.request.path
        modified_company = quote(PAYLOADS["find_company_drivers"], safe="")
        flow.request.path = "/find_company_drivers/" + modified_company

        mark_modified(
            flow,
            "/find_company_drivers/<company>",
            "company_path",
            original_path,
            flow.request.path,
        )
        return


def response(flow: http.HTTPFlow) -> None:
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "method": flow.request.method,
        "url": flow.request.pretty_url,
        "host": flow.request.host,
        "path": flow.request.path,
        "status_code": flow.response.status_code if flow.response else None,
        "sqli_modified": flow.metadata.get("sqli_modified", False),
        "sqli_changes": flow.metadata.get("sqli_changes", []),
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")