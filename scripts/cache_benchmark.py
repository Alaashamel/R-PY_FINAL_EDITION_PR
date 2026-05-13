"""Measure the visible effect of Redis cache-aside reads.

Run after starting the app and seeding demo data:
    python scripts/cache_benchmark.py --username patient1 --password patient123 --path /doctors/

The first request is normally a database read that fills Redis. The second request
should be served from cache and usually has a lower response time.
"""

from __future__ import annotations

import argparse
import statistics
import time
from typing import Any

import requests


def timed_get(url: str, headers: dict[str, str]) -> tuple[float, int, Any]:
    start = time.perf_counter()
    response = requests.get(url, headers=headers, timeout=10)
    elapsed_ms = (time.perf_counter() - start) * 1000
    try:
        body = response.json()
    except Exception:
        body = response.text
    return elapsed_ms, response.status_code, body


def login(base_url: str, username: str, password: str) -> str:
    response = requests.post(
        f"{base_url}/auth/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark FastAPI Redis cache-aside performance.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--username", default="patient1")
    parser.add_argument("--password", default="patient123")
    parser.add_argument("--path", default="/doctors/")
    parser.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()

    token = login(args.base_url, args.username, args.password)
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{args.base_url}{args.path}"

    first_ms, first_status, first_body = timed_get(url, headers)
    cached_times: list[float] = []
    for _ in range(args.runs):
        elapsed_ms, status, _ = timed_get(url, headers)
        if status != first_status:
            raise RuntimeError(f"Unexpected status change: first={first_status}, current={status}")
        cached_times.append(elapsed_ms)

    cached_avg = statistics.mean(cached_times)
    improvement = ((first_ms - cached_avg) / first_ms * 100) if first_ms else 0

    print("Cache benchmark result")
    print(f"URL: {url}")
    print(f"Status: {first_status}")
    print(f"Records returned: {len(first_body) if isinstance(first_body, list) else 'n/a'}")
    print(f"First request: {first_ms:.2f} ms")
    print(f"Cached average over {args.runs} runs: {cached_avg:.2f} ms")
    print(f"Estimated improvement: {improvement:.1f}%")


if __name__ == "__main__":
    main()
