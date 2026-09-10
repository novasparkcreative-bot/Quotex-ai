#!/usr/bin/env python3
"""Smoke-test a running local Quotex AI API.

This runner performs read-only checks only:
- GET /health must return HTTP 200 and {"status": "healthy"}
- GET /api/live/status must report live trading disabled with no expiry

It never calls the live enable/disable/execute endpoints and never places a trade.
"""

from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def get_json(url: str) -> tuple[int, object]:
    request = Request(url, headers={"Accept": "application/json"}, method="GET")
    with urlopen(request, timeout=5) as response:
        body = response.read().decode("utf-8")
        return response.status, json.loads(body)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only local API smoke test")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    checks: list[tuple[str, bool, str]] = []

    try:
        status_code, payload = get_json(f"{base_url}/health")
        ok = status_code == 200 and payload == {"status": "healthy"}
        checks.append(("health", ok, f"HTTP {status_code}, payload={payload!r}"))

        status_code, payload = get_json(f"{base_url}/api/live/status")
        expected = {"enabled": False, "expires_at": None}
        ok = status_code == 200 and payload == expected
        checks.append(("live-disabled", ok, f"HTTP {status_code}, payload={payload!r}"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"FAIL: unable to query {base_url}: {exc}", file=sys.stderr)
        return 1

    failed = False
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
        failed |= not ok

    if failed:
        print("Local API smoke test FAILED.")
        return 1

    print("Local API smoke test PASSED. No real-money trade was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
