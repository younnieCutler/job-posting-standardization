# Airflow Batch Orchestration Implementation Plan (5차시 과제)

**Goal:** Wrap the public ATS postings collector in an Airflow DAG that can be re-run with different parameters without code changes (5차시 requirement, due 2026-08-27 17:00), while making the collector's output match the "data keeps arriving" real-world posting cadence instead of a single overwritten snapshot.

**Context:** JDF's target architecture (README §3) is GCS Raw Zone → Spark Canonical mapping → BigQuery MERGE → dbt → Looker Studio, all batch. Real-time streaming (Kafka in the main pipeline) was explicitly rejected — job postings arrive on the order of days/weeks per company, not events per second; the existing Kafka work (4차시) stays a separate, already-graded track and is not touched here. BigQuery/dbt/Looker remain out of scope for this task — no GCP/dbt setup exists yet.

**Architecture:** Airflow `standalone` (SQLite + SequentialExecutor/LocalExecutor, single process) installed in a project-local venv on the host — reuses the host's existing Java/pyspark install directly, no Docker/Postgres/Celery needed (the DE-bootcamp Airflow 3.0 Celery+Redis+Flower stack from earlier lessons is overkill for one DAG). One DAG: collect (parameterized) → minimal Spark normalization → save.

**Tech Stack:** apache-airflow (venv, `airflow standalone`), existing `ingestion/collect_public_ats_postings.py` (unmodified logic, output path changed), pyspark (already installed on host, used in `streaming/spark_preprocess.py`).

---

### Decision: collector output must become partitioned, not overwritten

**Problem:** `write_output()` in `ingestion/collect_public_ats_postings.py` opens `data/golden-set/public-it-postings.csv` in `"w"` mode — every run replaces the previous run's file entirely. Scheduling this `@daily` in Airflow would not accumulate history; it would just refresh a single snapshot, which defeats "data keeps arriving" and gives BigQuery MERGE (later) nothing to diff against.

**Fix:** Partition output by run date, mirroring the existing `data/raw/<platform>/*.parquet` convention:
```
data/golden-set/public-it-postings/dt=<YYYY-MM-DD>/postings.csv
data/golden-set/public-it-postings/dt=<YYYY-MM-DD>/manifest.json
```
Cross-run dedup is deferred to the BigQuery MERGE stage (later session) using the same `posting_id = sha256(source_platform + source_posting_id)` pattern already used by the synthetic generator — `source_record_sha256` (already computed per record) is the input to that key. Within a single run, the existing `prepare_records()` dedup is untouched.

### Task 1: Add `--run-date` and partitioned output to the collector

**Files:**
- Modify: `tests/test_collect_public_ats_postings.py`
- Modify: `ingestion/collect_public_ats_postings.py`

- [x] Write a failing test: `default_paths("2026-08-25")` returns paths ending in `dt=2026-08-25/postings.csv` and `dt=2026-08-25/manifest.json`.
- [x] Add a `--run-date` CLI arg (default: today, `YYYY-MM-DD`) and a `default_paths()` helper that builds the `dt=` partition path from it; `--output`/`--manifest` still override when passed explicitly.
- [x] Re-run `python -m unittest tests.test_collect_public_ats_postings -v`; PASS (7/7).
- [x] Migrated yesterday's flat snapshot (`public-it-postings.csv`, 188MB, gitignored) into `dt=2026-08-24/`; updated `.gitignore` to match the new partitioned path.
- [x] Commit: `feat: partition ATS collector output by run date` (88d871a).

### Task 2: Minimal Spark normalization for collected postings

**Files:**
- Create: `ingestion/spark_normalize_public_postings.py`

- [x] Read one `dt=` partition's `postings.csv`, apply NFKC normalization to `title`/`description`, compute `posting_id = sha2(source_platform+source_posting_id, 256)`.
- [x] Write result to `data/golden-set/public-it-postings-canonical/dt=<date>/*.parquet`; print before/after row counts.
- [x] Verified against `dt=2026-08-24`: before=23302, after=23302, 0 duplicate `posting_id`. Commit `a47fd36`.

### Task 3: Airflow DAG wrapping collect → normalize

**Files:**
- Create: `dags/collect_postings_dag.py`
- Create: `requirements-airflow.txt` (separate from `requirements.txt` — Airflow's dependency set is heavy and unrelated to the core pipeline)

- [ ] `python3 -m venv .venv-airflow && source .venv-airflow/bin/activate && pip install "apache-airflow==3.3.1" --constraint <official constraints URL for the installed Python version>`.
- [ ] DAG `collect_public_postings`, schedule `@daily`, `params` exposing `companies` (int, default 300), `limit` (optional int), `catalog_url` (string, default `DEFAULT_CATALOG`) — these map directly onto the collector's existing argparse flags, satisfying the "re-run with different input, no code changes" requirement.
- [ ] Task 1 (`BashOperator` or `PythonOperator`): run `collect_public_ats_postings.main()` with the DAG run's params and `--run-date {{ ds }}`.
- [ ] Task 2: run `spark_normalize_public_postings.py` against that same `dt=` partition.
- [ ] `airflow standalone` locally, trigger the DAG twice with different `companies`/`limit` values, screenshot both runs + logs for submission.

### Task 4: README — 5차시 section

**Files:**
- Modify: `README.md`

- [ ] Add a "5차시 과제 — Airflow 배치 자동화" section (same style as the existing 4차시 section): run commands, DAG params table, what re-running with different params produces, explicit "실제 구현 vs 계획" line noting BigQuery/dbt/Looker are still not implemented.

---

## Explicitly out of scope for this task

- BigQuery MERGE, dbt models, Looker Studio dashboard — no GCP/dbt setup exists; deferred to a later session per README §4.
- Any change to the Kafka/Spark synthetic-data track from 4차시 (`streaming/*.py`, `docker-compose.yml`) — stays as-is, already submitted.
- Real-time/streaming ingestion of ATS postings — rejected; postings arrive slowly enough that daily polling is the correct match (see conversation 2026-08-25).
