"""4차시 과제용 Spark 배치 정규화 (실채용공고, ATS 수집기 결과).

data/golden-set/public-it-postings/dt=<run-date>/postings.csv 를 읽어
(1) title/description NFKC 정규화 (2) posting_id = sha256(source_platform+source_posting_id)
계산 (3) posting_id 중복 제거 후
data/golden-set/public-it-postings-canonical/dt=<run-date>/*.parquet 로 저장한다.

Usage: python ingestion/spark_normalize_public_postings.py --run-date 2026-08-24
"""
import argparse
import os
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

os.environ.pop("SPARK_HOME", None)  # stale local SPARK_HOME breaks pyspark's bundled spark-submit

from pyspark.sql import SparkSession
from pyspark.sql.functions import concat_ws, sha2, udf
from pyspark.sql.types import StringType

REPO_ROOT = Path(__file__).resolve().parent.parent
PARTITION_ROOT = REPO_ROOT / "data" / "golden-set" / "public-it-postings"
CANONICAL_ROOT = REPO_ROOT / "data" / "golden-set" / "public-it-postings-canonical"

nfkc_normalize = udf(lambda s: unicodedata.normalize("NFKC", s) if s else s, StringType())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-date", default=datetime.now(timezone.utc).date().isoformat())
    args = parser.parse_args(argv)

    input_file = PARTITION_ROOT / f"dt={args.run_date}" / "postings.csv"
    output_dir = CANONICAL_ROOT / f"dt={args.run_date}"
    output_dir.mkdir(parents=True, exist_ok=True)

    spark = SparkSession.builder.appName("jdf-5th-assignment-normalize").master("local[*]").getOrCreate()

    df = spark.read.option("header", True).csv(str(input_file))
    before = df.count()

    df = df.withColumn("title_normalized", nfkc_normalize(df["title"]))
    df = df.withColumn("description_normalized", nfkc_normalize(df["description"]))
    df = df.withColumn("posting_id", sha2(concat_ws("", df["source_platform"], df["source_posting_id"]), 256))
    df = df.dropDuplicates(["posting_id"])

    after = df.count()

    df.write.mode("overwrite").parquet(str(output_dir))
    spark.stop()

    print(f"before={before} after={after} saved_to={output_dir} run_date={args.run_date}")


if __name__ == "__main__":
    main()
