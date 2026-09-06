#!/usr/bin/env python3
"""cloud/query_marts.py — BigQuery 서빙 장면 (SQL 조회).

    python cloud/query_marts.py

jdf.postings_canonical / mart_tech_demand / mart_platform_dist 를 조회해
행수와 상위값을 출력한다. 발표 "저장 결과를 쓰는 장면" 캡처용.
"""
from __future__ import annotations

import os

from google.cloud import bigquery

PROJECT = os.environ.get("JDF_GCP_PROJECT", "bright-link-507313-q3")
DATASET = os.environ.get("JDF_BQ_DATASET", "jdf")
LOCATION = os.environ.get("JDF_GCP_REGION", "asia-northeast1")


def show(client: bigquery.Client, title: str, sql: str) -> None:
    print(f"\n── {title}\n{sql.strip()}")
    for row in client.query(sql).result():
        print("   " + " | ".join(f"{k}={v}" for k, v in row.items()))


def main() -> None:
    c = bigquery.Client(project=PROJECT, location=LOCATION)
    ds = f"{PROJECT}.{DATASET}"
    show(c, "canonical 총계", f"SELECT COUNT(*) AS n FROM `{ds}.postings_canonical`")
    show(c, "canonical 상위 10행",
         f"SELECT posting_id, source_platform, company_name, tier "
         f"FROM `{ds}.postings_canonical` ORDER BY posting_id LIMIT 10")
    show(c, "mart_tech_demand 상위 10",
         f"SELECT skill, postings FROM `{ds}.mart_tech_demand` "
         f"ORDER BY postings DESC LIMIT 10")
    show(c, "mart_platform_dist",
         f"SELECT * FROM `{ds}.mart_platform_dist` ORDER BY postings DESC")


if __name__ == "__main__":
    main()
