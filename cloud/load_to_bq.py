#!/usr/bin/env python3
"""cloud/load_to_bq.py — GCS parquet → BQ staging → MERGE INTO canonical.

    python cloud/load_to_bq.py --run-date 2026-09-06

1. gs://<bucket>/canonical/dt=<run-date>/*.parquet 를 jdf.staging_postings 로
   적재 (WRITE_TRUNCATE, run_date 컬럼 주입).
2. MERGE INTO jdf.postings_canonical USING staging ON posting_id
   (matched=UPDATE, not matched=INSERT) — 멱등.
출력: staging_rows / updated / inserted / canonical_total

alert 가드: staging_rows == 0 이면 raise (빈 입력이면 실패시켜 알림 발화).
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys

from google.cloud import bigquery

DEFAULT_PROJECT = os.environ.get("JDF_GCP_PROJECT", "bright-link-507313-q3")
DEFAULT_BUCKET = os.environ.get("JDF_GCS_BUCKET", "bright-link-507313-q3-jdf-raw")
DEFAULT_DATASET = os.environ.get("JDF_BQ_DATASET", "jdf")
DEFAULT_LOCATION = os.environ.get("JDF_GCP_REGION", "asia-northeast1")
KEY = "posting_id"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-date", default=dt.date.today().isoformat())
    p.add_argument("--project", default=DEFAULT_PROJECT)
    p.add_argument("--bucket", default=DEFAULT_BUCKET)
    p.add_argument("--dataset", default=DEFAULT_DATASET)
    p.add_argument("--prefix", default="canonical")
    p.add_argument("--location", default=DEFAULT_LOCATION)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    client = bigquery.Client(project=args.project, location=args.location)
    ds = f"{args.project}.{args.dataset}"
    staging = f"{ds}.staging_postings"
    canonical = f"{ds}.postings_canonical"
    uri = f"gs://{args.bucket}/{args.prefix}/dt={args.run_date}/*.parquet"

    # 1. load → staging (WRITE_TRUNCATE)
    load_cfg = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    print(f"▶ load {uri} -> {staging}")
    client.load_table_from_uri(uri, staging, job_config=load_cfg).result()

    # run_date 주입 (parquet 에 없으므로 컬럼 추가 후 채움)
    client.query(
        f"ALTER TABLE `{staging}` ADD COLUMN IF NOT EXISTS run_date DATE"
    ).result()
    client.query(
        f"UPDATE `{staging}` SET run_date = DATE('{args.run_date}') WHERE TRUE"
    ).result()

    staging_tbl = client.get_table(staging)
    staging_rows = staging_tbl.num_rows
    print(f"staging_rows={staging_rows}")
    if staging_rows == 0:
        raise SystemExit("staging_rows == 0 — 빈 입력. MERGE 중단 (alert 트리거).")

    cols = [f.name for f in staging_tbl.schema]
    if KEY not in cols:
        raise SystemExit(f"staging 에 키 컬럼 {KEY} 없음: {cols}")

    # 2. MERGE (canonical 없으면 먼저 생성)
    client.query(
        f"CREATE TABLE IF NOT EXISTS `{canonical}` AS "
        f"SELECT * FROM `{staging}` WHERE FALSE"
    ).result()

    set_clause = ", ".join(f"T.{c} = S.{c}" for c in cols if c != KEY)
    insert_cols = ", ".join(cols)
    insert_vals = ", ".join(f"S.{c}" for c in cols)
    merge_sql = f"""
    MERGE `{canonical}` T
    USING `{staging}` S
    ON T.{KEY} = S.{KEY}
    WHEN MATCHED THEN UPDATE SET {set_clause}
    WHEN NOT MATCHED THEN INSERT ({insert_cols}) VALUES ({insert_vals})
    """
    merge_job = client.query(merge_sql)
    merge_job.result()
    dml = merge_job.dml_stats  # DmlStats(inserted_row_count, updated_row_count, ...)
    inserted = getattr(dml, "inserted_row_count", None)
    updated = getattr(dml, "updated_row_count", None)

    canonical_total = list(client.query(
        f"SELECT COUNT(*) AS n FROM `{canonical}`"
    ).result())[0].n

    print(f"updated={updated} inserted={inserted} canonical_total={canonical_total}")


if __name__ == "__main__":
    main()
