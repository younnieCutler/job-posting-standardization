#!/usr/bin/env python3
"""cloud/upload_to_gcs.py — 최종 parquet 을 GCS canonical 존으로 업로드.

    python cloud/upload_to_gcs.py --run-date 2026-09-06

기본 소스는 합성 트랙 산출물(data/processed/postings_clean.parquet).
gs://<bucket>/canonical/dt=<run-date>/ 아래에 part 파일을 그대로 올린다.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import pathlib
import sys

from google.cloud import storage

DEFAULT_BUCKET = os.environ.get("JDF_GCS_BUCKET", "bright-link-507313-q3-jdf-raw")
DEFAULT_SRC = "data/processed/postings_clean.parquet"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-date", default=dt.date.today().isoformat())
    p.add_argument("--src", default=DEFAULT_SRC,
                   help="parquet 파일 또는 디렉토리 (Spark 출력은 디렉토리)")
    p.add_argument("--bucket", default=DEFAULT_BUCKET)
    p.add_argument("--prefix", default="canonical",
                   help="gs://<bucket>/<prefix>/dt=<run-date>/")
    return p.parse_args()


def iter_parquet_files(src: pathlib.Path):
    if src.is_dir():
        files = sorted(f for f in src.glob("*.parquet"))
        if not files:
            sys.exit(f"parquet 파일 없음: {src}")
        return files
    if src.is_file():
        return [src]
    sys.exit(f"소스 경로 없음: {src}")


def main() -> None:
    args = parse_args()
    src = pathlib.Path(args.src)
    files = iter_parquet_files(src)

    client = storage.Client()
    bucket = client.bucket(args.bucket)
    dest_dir = f"{args.prefix}/dt={args.run_date}"

    total_bytes = 0
    for f in files:
        blob = bucket.blob(f"{dest_dir}/{f.name}")
        blob.upload_from_filename(str(f))
        size = f.stat().st_size
        total_bytes += size
        print(f"  {f.name} -> gs://{args.bucket}/{dest_dir}/{f.name} ({size:,} B)")

    print(f"uploaded files={len(files)} bytes={total_bytes:,} "
          f"dest=gs://{args.bucket}/{dest_dir}/")


if __name__ == "__main__":
    main()
