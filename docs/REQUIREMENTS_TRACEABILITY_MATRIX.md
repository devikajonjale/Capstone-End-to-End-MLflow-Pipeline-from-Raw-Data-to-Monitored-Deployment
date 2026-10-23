# Requirements Traceability Matrix

Every task and functional requirement in the Project 4 brief, mapped to the
concrete source files, tests and evidence artefacts that satisfy it.

## Task 1: Problem framing and lifecycle map

| Requirement | Implementation | Evidence |
|---|---|---|
| Two-page design note | `DESIGN_NOTE.md`, Section 01 of report | design note file, report cover |
| Architecture diagram | lifecycle flow in report Section 01; mapping table | report Figure in Section 01 |
| Numeric, justified success thresholds | `config/config.yaml` `model_gate` + report Section 01 | config excerpt in report Section 03 |
| Lifecycle traceability (every component to a stage) | mapping table in report Section 02 | report table in Section 02 |

## Task 2: Configuration, code and data management

| Requirement | Implementation | Evidence |
|---|---|---|
| Single YAML source of truth | `config/config.yaml` | report Section 03 |
| Validated on load | `src/config_loader.py` (`ConfigValidationError`) | `tests/test_config.py` |
| No hard-coded paths or thresholds | all stages read from `config` | code review in Section 03 |
| Fresh clone reproduces the metrics | pinned `requirements.txt`, fixed random_state, data hash per run | `tests/test_config.py`, lineage JSON |
| Versioned data | `.dvc/`, data in Git, SHA-256 of raw CSV in lineage | `/lineage` endpoint |

## Task 3: Pipeline design

| Requirement | Implementation | Evidence |
|---|---|---|
| Orchestrated workflow with separate stages | Prefect flows in `src/pipeline.py` | report Section 05 |
| Each stage has defined inputs and outputs | plain functions in `src/stages/*` | per-stage docstrings, Section 05 table |
| Each stage re-runnable on its own | tests call stages directly | `tests/test_*.py` |
| Workflow graph matches code | report flow diagrams in Sections 05 and 11 | diagram in Section 05 |
| Stage-level logs and run history | Prefect task runs + Python logging | screenshot placeholder, Section 05 |

## Task 4: Validation gates and safe failure

| Requirement | Implementation | Evidence |
|---|---|---|
| Data gate (schema, ranges, missing limit) | `src/stages/validate_data.py` | report Section 08.1 |
| Model gate (quality threshold + Champion vs Challenger) | `src/stages/evaluate.py` | report Section 08.2 |
| Two failing scenarios demonstrated | `scripts/demo_failures.py` | code block in Section 08.3 |
| Production model unchanged after failure | version prints before/after in demo | demo output in Section 08.3 |
| Gate thresholds configurable | `config/model_gate.*` | config excerpt Section 03 |

## Task 5: Tracking, registry and lineage

| Requirement | Implementation | Evidence |
|---|---|---|
| Every run tracked | MLflow runs in `src/stages/train.py` | 4 runs per training (3 candidates + parent) |
| Models registered with stage transitions | `src/stages/register.py` | screenshot placeholder, report Section 09 |
| Stage transitions only via pipeline | `register_model()` is the only promotion path | code review of `register.py` |
| Live lineage demo from deployed model | `/lineage` endpoint + `models/production/lineage.json` | JSON block in Section 09 |
| Lineage includes code version, data version, config, run | git commit + raw CSV SHA-256 + config_version + run_id in record | `/lineage` sample |

## Task 6: Automated build and release

| Requirement | Implementation | Evidence |
|---|---|---|
| PR triggers tests and lightweight pipeline | `.github/workflows/ci.yml` | screenshot placeholder, Section 12 |
| Passing and failing PR in history | PR #1 (quick-wins) + PR #3 (`test/deliberately-failing-ci-gate`) | GitHub Actions page |
| Merge to main builds a deployable image | `.github/workflows/release.yml` (push to main) | release workflow in `.github/` |
| At least one release | `v1.0.0` tag + Releases page | screenshot placeholder, Section 12 |
| Image tagged so container links to commit | image carries commit SHA as tag + label | `release.yml`, `Dockerfile` ARG |
| Rollback procedure written and tested | `ROLLBACK.md` | handover record + rollback test |

## Task 7: Serving and monitoring

| Requirement | Implementation | Evidence |
|---|---|---|
| Model served as containerised API | `Dockerfile`, `docker-compose.yml` | report Section 13 |
| Operational metrics (latency, throughput, errors, price distribution) | `src/serving/app.py` Prometheus instruments | report Section 11.4 + load test |
| Dashboard or report over the three batches | `data/results/monitoring_report.md` | report Section 11 table |
| Data drift measured | PSI per feature, `src/stages/monitor.py` | report Section 11.2 |
| Performance drift (because batches have prices) | ratio to validated RMSE in `src/stages/monitor.py` | report Section 11.3 |
| Alert thresholds justified | `config.monitoring.psi_*` + `performance_alert_ratio` | config excerpt Section 03 |
| Alerted batches identified with evidence | monitoring report plus Section 11 | monitoring report file |
| Response to an alert documented | runbook flow in Section 11.4 | flowchart Section 11.4 |

## Task 8: Final demonstration

| Requirement | Implementation | Evidence |
|---|---|---|
| 5 to 10 minute demonstration script | report Section 14 worked example | step-by-step section with real output |
| Every member can explain their part | contributions in Section 15, two merged PRs under both names | Git commit history, PR authors |
| Failure scenario shown as safe | demo output in Section 08.3 | code block |

## Deliverables checklist

| Deliverable | Status | Location |
|---|---|---|
| Repository with pipeline, config, tests, workflows, Dockerfile, README | Done | main branch |
| Design note (<=2 pages) with architecture diagram | Done | `DESIGN_NOTE.md`, report Section 01 |
| Workflow graph, run history, registry screenshots | Partial | report placeholders ready; Prefect + MLflow screenshots to drop in |
| Evidence of two failing-gate scenarios | Done | `scripts/demo_failures.py` + Section 08.3 |
| Lineage demonstration | Done | `/lineage` endpoint, `models/production/lineage.json` |
| CI history including at least one release | Done after Step 4 of handoff (tag `v1.0.0`) | GitHub Actions + Releases |
| Monitoring report over 3 batches | Done | `data/results/monitoring_report.md` |
| 5 to 10 minute demonstration | Script ready, recording to be made | report Section 14 |
| One-page reflection | Done | report Section 15.2 |
