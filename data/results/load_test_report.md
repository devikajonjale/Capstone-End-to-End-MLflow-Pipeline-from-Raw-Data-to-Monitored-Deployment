# Load test report

Captured by Saachi on 2026-10-22 against the containerised service running
locally on Docker Desktop 28.0.4. Reproduce with:

```bash
python -m scripts.load_test --requests 500 --workers 8
```

- URL: `http://localhost:8000`
- Total requests: **110+** (randomised listings, mixed zones and sizes)
- Duration: continuous over the live Grafana session
- Errors: **0** (100% success rate)
- Status counts: `{200: 110+}`

## Latency (ms)

| avg | p50 | p95 | p99 | max |
|---|---|---|---|---|
| ~18 | ~15 | 36.8 | ~55 | ~70 |

Measured directly from the Prometheus histogram
`prediction_latency_seconds` scraped at ten second intervals from the running
`app:8000` service.

## SLA compliance

| Metric | Target | Observed | Verdict |
|---|---|---|---|
| Average latency | < 30 ms | ~18 ms | PASS |
| p95 latency | < 50 ms | 36.8 ms | PASS |
| p99 latency | < 100 ms | ~55 ms | PASS |
| Error rate | < 1% | 0% | PASS |

See `handover/SAACHI_EVIDENCE_RECORD.md` for the full operational verification
log, including the Prometheus and Grafana screenshots at
`handover/evidence/`.
