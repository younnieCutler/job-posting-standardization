"""4차시 과제용 Spark 배치 전처리.

data/kafka_landed/postings.jsonl(Consumer 산출물)을 읽어
(1) raw_title NFKC 정규화 (2) posting_id 중복 제거 (3) is_negative_control 제외
후 data/processed/postings_clean.parquet로 저장한다.

Usage: python streaming/spark_preprocess.py
"""
import unicodedata
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

REPO_ROOT = Path(__file__).resolve().parent.parent
LANDED_FILE = REPO_ROOT / "data" / "kafka_landed" / "postings.jsonl"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
PROCESSED_FILE = PROCESSED_DIR / "postings_clean.parquet"

nfkc_normalize = udf(lambda s: unicodedata.normalize("NFKC", s) if s else s, StringType())


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    spark = SparkSession.builder.appName("jdf-4th-assignment-preprocess").master("local[*]").getOrCreate()

    df = spark.read.json(str(LANDED_FILE))
    before = df.count()

    df = df.withColumn("raw_title_normalized", nfkc_normalize(df["raw_title"]))
    df = df.dropDuplicates(["posting_id"])
    df = df.filter(df["is_negative_control"] == False)  # noqa: E712

    after = df.count()

    df.write.mode("overwrite").parquet(str(PROCESSED_FILE))
    spark.stop()

    print(f"before={before} after={after} saved_to={PROCESSED_FILE}")


if __name__ == "__main__":
    main()
