"""Drive load at the running prediction service and report telemetry.

Sends a configurable number of concurrent /predict requests with randomised
listings and records latency percentiles, throughput and error rate. Writes a
Markdown summary into data/results/load_test_report.md that the project report
can cite as evidence of operational performance.

Usage:
    python -m scripts.load_test                    # defaults: 500 requests, 8 workers
    python -m scripts.load_test --requests 2000 --workers 16
    python -m scripts.load_test --url http://localhost:8000
"""
import argparse
import json
import os
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

ZONES = ["North", "South", "East", "West", "Central"]
CONDITIONS = ["Poor", "Fair", "Good", "Excellent"]


def random_listing(rng: random.Random) -> dict:
    return {
        "Area_sqft": rng.randint(400, 2500),
        "Bedrooms": rng.randint(1, 5),
        "Bathrooms": rng.randint(1, 4),
        "Age_Years": rng.randint(0, 60),
        "Distance_to_Center_km": round(rng.uniform(1, 30), 1),
        "Neighborhood_Score": round(rng.uniform(2, 9), 1),
        "Has_Parking": rng.randint(0, 1),
        "Property_Condition": rng.choice(CONDITIONS),
        "City_Zone": rng.choice(ZONES),
    }


def one_request(url: str, payload: dict, timeout: float = 5.0) -> tuple[int, float]:
    start = time.perf_counter()
    try:
        r = requests.post(url + "/predict", json=payload, timeout=timeout)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return r.status_code, elapsed_ms
    except Exception:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return 599, elapsed_ms  # synthetic client-side error code


def run(url: str, n: int, workers: int) -> dict:
    rng = random.Random(42)
    payloads = [random_listing(rng) for _ in range(n)]

    latencies: list[float] = []
    status_counts: dict[int, int] = {}

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(one_request, url, p) for p in payloads]
        for fut in as_completed(futures):
            code, ms = fut.result()
            latencies.append(ms)
            status_counts[code] = status_counts.get(code, 0) + 1
    total_s = time.perf_counter() - t0

    latencies.sort()
    def q(p: float) -> float:
        idx = min(len(latencies) - 1, int(round((len(latencies) - 1) * p)))
        return latencies[idx]

    errors = sum(c for code, c in status_counts.items() if code >= 400)
    return {
        "url": url,
        "requests": n,
        "workers": workers,
        "duration_s": round(total_s, 3),
        "throughput_rps": round(n / total_s, 1) if total_s > 0 else 0.0,
        "error_count": errors,
        "error_rate_pct": round(100 * errors / n, 3),
        "status_counts": status_counts,
        "latency_ms": {
            "avg": round(statistics.fmean(latencies), 2),
            "p50": round(q(0.50), 2),
            "p95": round(q(0.95), 2),
            "p99": round(q(0.99), 2),
            "max": round(max(latencies), 2),
        },
    }


def write_report(result: dict, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    md_path = os.path.join(out_dir, "load_test_report.md")
    lat = result["latency_ms"]
    with open(md_path, "w") as f:
        f.write("# Load test report\n\n")
        f.write(f"- URL: `{result['url']}`\n")
        f.write(f"- Total requests: **{result['requests']}** across {result['workers']} workers\n")
        f.write(f"- Duration: **{result['duration_s']} s**, throughput **{result['throughput_rps']} req/s**\n")
        f.write(f"- Errors: **{result['error_count']}** ({result['error_rate_pct']}%)\n")
        f.write(f"- Status counts: {result['status_counts']}\n\n")
        f.write("## Latency (ms)\n\n")
        f.write("| avg | p50 | p95 | p99 | max |\n|---|---|---|---|---|\n")
        f.write(f"| {lat['avg']} | {lat['p50']} | {lat['p95']} | {lat['p99']} | {lat['max']} |\n\n")
        f.write("## SLA compliance (reference targets)\n\n")
        f.write("| Metric | Target | Observed | Verdict |\n|---|---|---|---|\n")
        f.write(f"| Average latency | < 30 ms | {lat['avg']} ms | {'PASS' if lat['avg'] < 30 else 'FAIL'} |\n")
        f.write(f"| p95 latency | < 50 ms | {lat['p95']} ms | {'PASS' if lat['p95'] < 50 else 'FAIL'} |\n")
        f.write(f"| p99 latency | < 100 ms | {lat['p99']} ms | {'PASS' if lat['p99'] < 100 else 'FAIL'} |\n")
        f.write(f"| Error rate | < 1% | {result['error_rate_pct']}% | {'PASS' if result['error_rate_pct'] < 1 else 'FAIL'} |\n")
    json_path = os.path.join(out_dir, "load_test_report.json")
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
    return md_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--requests", type=int, default=500)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out-dir", default="data/results")
    args = ap.parse_args()
    result = run(args.url, args.requests, args.workers)
    md = write_report(result, args.out_dir)
    print(json.dumps(result, indent=2))
    print(f"\nWrote {md}")


if __name__ == "__main__":
    main()
