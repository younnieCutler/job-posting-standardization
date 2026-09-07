#!/usr/bin/env python3
"""cloud/load_ats_to_bq.py — Public ATS canonical parquet → BigQuery jdf.ats_postings.

    python cloud/load_ats_to_bq.py --run-date 2026-08-30-scaleup

로컬 parquet 디렉토리를 읽어 jdf.ats_postings 로 WRITE_TRUNCATE 적재한다.
합성 트랙(postings_canonical)과 스키마가 다르므로 별도 테이블. MERGE 안 함(스냅샷).
출력: rows / companies / platforms.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

import pandas as pd
from google.cloud import bigquery

PROJECT = os.environ.get("JDF_GCP_PROJECT", "bright-link-507313-q3")
DATASET = os.environ.get("JDF_BQ_DATASET", "jdf")
LOCATION = os.environ.get("JDF_GCP_REGION", "asia-northeast1")
ROOT = "data/golden-set/public-it-postings-canonical"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-date", help="dt=<run-date> 파티션. 생략 시 최신")
    p.add_argument("--project", default=PROJECT)
    p.add_argument("--dataset", default=DATASET)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if args.run_date:
        src = f"{ROOT}/dt={args.run_date}"
    else:
        parts = sorted(glob.glob(f"{ROOT}/dt=*/"))
        if not parts:
            sys.exit(f"파티션 없음: {ROOT}")
        src = parts[-1].rstrip("/")
    files = sorted(glob.glob(f"{src}/*.parquet"))
    if not files:
        sys.exit(f"parquet 없음: {src}")

    df = pd.concat((pd.read_parquet(f) for f in files), ignore_index=True)
    df["run_date"] = os.path.basename(src).removeprefix("dt=")
    print(f"src={src} rows={len(df)}")

    table = f"{args.project}.{args.dataset}.ats_postings"
    client = bigquery.Client(project=args.project, location=LOCATION)
    job = client.load_table_from_dataframe(
        df, table,
        job_config=bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
        ),
    )
    job.result()

    n = client.get_table(table).num_rows
    companies = list(client.query(
        f"SELECT COUNT(DISTINCT company_name) c FROM `{table}`"
    ).result())[0].c
    plats = {r.source_platform: r.n for r in client.query(
        f"SELECT source_platform, COUNT(*) n FROM `{table}` GROUP BY 1 ORDER BY n DESC"
    ).result()}
    print(f"loaded {table}: rows={n} companies={companies} platforms={plats}")


if __name__ == "__main__":
    main()
