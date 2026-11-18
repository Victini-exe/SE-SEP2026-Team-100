"""Build the Milestone 3 test-case document from a pytest run.

Usage (from backend/):
    python -m pytest tests --case-report ../docs/testing/api-test-results.json
    python tests/generate_test_case_doc.py ../docs/testing/api-test-results.json ../docs/testing/API_TEST_CASES.md

Every case is written in the course format: API being tested, Inputs,
Expected output, Actual output, Result (Success/Fail).  The actual output and
the result come from the real run, so re-run both commands after any change.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

SECTIONS = {
    "test_api_auth": "Authentication and health",
    "test_api_students": "Student profile and career questions",
    "test_api_mentors": "Mentor applications, profiles, search and public profiles",
    "test_api_admin_applications": "Admin: mentor verification, dashboard and users",
    "test_api_matching": "Matching and recommendations",
    "test_api_requests": "Mentoring requests",
    "test_api_relationships": "Relationships, sessions, notes and messages",
    "test_api_moderation_insights": "Reports, moderation, alerts, analytics and notifications",
}
MAX_STRING = 90


def shorten(value):
    """Keep the document readable: long strings and tokens are summarised."""
    if isinstance(value, dict):
        return {k: ("<JWT access token>" if k == "access_token" else shorten(v)) for k, v in value.items()}
    if isinstance(value, list):
        if len(value) > 6:
            return [shorten(v) for v in value[:5]] + [f"... {len(value) - 5} more items"]
        return [shorten(v) for v in value]
    if isinstance(value, str) and len(value) > MAX_STRING:
        if len(set(value)) <= 2:
            return f"<{len(value)} characters: {value[:12]!r}...>"
        return value[:60] + f"... ({len(value)} characters)"
    return value


def route(path: str) -> str:
    """/api/v1/requests/12/decision -> /api/v1/requests/{id}/decision"""
    return "/".join("{id}" if part.isdigit() else part for part in path.split("/"))


def as_json(value) -> str:
    return json.dumps(shorten(value), ensure_ascii=False)


def case_title(case: dict) -> str:
    title = case["title"]
    if "[" in case["nodeid"]:
        title += f" [{case['nodeid'].rsplit('[', 1)[1].rstrip(']')}]"
    return title


def expected_lines(call: dict) -> list[str]:
    expected = call.get("expected") or {}
    if not expected:
        return ["- (no expectation recorded for this call)"]
    lines = [f"- HTTP Status Code: {expected['status']}"]
    if expected.get("body") is not None:
        lines.append(f"- JSON: `{as_json(expected['body'])}`")
    elif expected.get("contains") is not None:
        lines.append(f"- JSON containing: `{as_json(expected['contains'])}`")
    elif expected["status"] == 422:
        lines.append("- JSON: validation error (`detail` lists the invalid field)")
    if expected.get("note"):
        lines.append(f"- Also: {expected['note']}")
    return lines


def input_lines(call: dict) -> list[str]:
    lines = [f"- Request Method: {call['method']}"]
    if call.get("actor"):
        lines.append(f"- Header: `Authorization: Bearer <{call['actor']} token>`")
    else:
        lines.append("- Header: none (not logged in)")
    if call.get("params"):
        lines.append(f"- Query: `{as_json(call['params'])}`")
    if call.get("json") is not None:
        lines.append(f"- JSON: `{as_json(call['json'])}`")
    if call.get("form"):
        form = {k: ("<password>" if k == "password" else v) for k, v in call["form"].items()}
        lines.append(f"- Form data: `{as_json(form)}`")
    return lines


def render_case(number: int, case: dict) -> list[str]:
    out = [f"### TC-{number:03d}: {case_title(case)}", ""]
    if case["stories"]:
        out += [f"**User stories:** {', '.join(case['stories'])}", ""]
    if case["description"]:
        out += [case["description"], ""]
    calls = case["calls"]
    if not calls:
        out += [
            "**Function being tested:** `app.services.matching.calculate_match` (unit test, no HTTP call)",
            "",
            f"**Inputs / expected output:** see `{case['nodeid']}`",
            "",
        ]
    for index, call in enumerate(calls, start=1):
        prefix = f"Step {index}: " if len(calls) > 1 else ""
        out += [f"**{prefix}API being tested:** `{call['method']} {call['path']}`", "", "**Inputs:**", *input_lines(call), ""]
        out += ["**Expected Output:**", *expected_lines(call), ""]
        out += ["**Actual Output:**", f"- HTTP Status Code: {call['status']}", f"- JSON: `{as_json(call['response'])}`", ""]
    out.append(f"**Result:** {case['result']}")
    if case.get("known_defect"):
        out.append(f"\n> **Defect found:** {case['known_defect']}")
    elif case["result"] == "Fail" and case.get("error"):
        out.append(f"\n> **Failure:** {case['error']}")
    out += ["", f"pytest: `{case['nodeid']}`", "", "---", ""]
    return out


def main(source: str, target: str) -> None:
    data = json.loads(Path(source).read_text(encoding="utf-8"))
    order = list(SECTIONS)
    cases = sorted((c for c in data["cases"] if c["module"] in SECTIONS), key=lambda c: order.index(c["module"]))
    counts = Counter(c["result"] for c in cases)
    defects = [c for c in cases if c["result"] == "Fail"]
    endpoints = sorted({f"{call['method']} {route(call['path'])}" for c in cases for call in c["calls"]})

    out = [
        "# Milestone 3 - API test cases",
        "",
        f"Generated from a real pytest run on {data['generated_at'][:19].replace('T', ' ')} UTC. "
        "Inputs, expected output and actual output are recorded by the test suite itself.",
        "",
        "| | Count |",
        "|---|---|",
        f"| Test cases | {len(cases)} |",
        f"| Success | {counts.get('Success', 0)} |",
        f"| Fail | {counts.get('Fail', 0)} |",
        f"| Endpoints exercised (method + route) | {len(endpoints)} |",
        "",
        "Endpoints covered: " + ", ".join(f"`{e}`" for e in endpoints),
        "",
        "## Defects found by testing (actual output differs from expected)",
        "",
        "| Test case | API | Defect |",
        "|---|---|---|",
    ]
    numbered = {c["nodeid"]: n for n, c in enumerate(cases, start=1)}
    for case in defects:
        api = f"`{case['calls'][-1]['method']} {case['calls'][-1]['path']}`" if case["calls"] else "-"
        reason = case.get("known_defect") or case.get("error") or ""
        out.append(f"| TC-{numbered[case['nodeid']]:03d} {case['title']} | {api} | {reason} |")
    if not defects:
        out.append("| - | - | No failing cases |")
    out += ["", "## How to run", "", "```bash", "cd backend", "python -m pytest -v -rxX", "```", ""]

    for module, heading in SECTIONS.items():
        section = [c for c in cases if c["module"] == module]
        if not section:
            continue
        out += [f"## {heading}", "", f"Source: `backend/tests/{module}.py`", ""]
        for case in section:
            out += render_case(numbered[case["nodeid"]], case)

    Path(target).parent.mkdir(parents=True, exist_ok=True)
    Path(target).write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {len(cases)} test cases ({counts.get('Success', 0)} success, {counts.get('Fail', 0)} fail) to {target}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python tests/generate_test_case_doc.py RESULTS.json OUTPUT.md")
    main(sys.argv[1], sys.argv[2])
