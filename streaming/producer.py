"""4차시 과제용 Kafka Producer.

data/raw/<platform>/*.parquet(기존 생성기 산출물)를 읽어 row마다 JSON으로
직렬화해 Kafka topic으로 전송한다. 생성기(ingestion/)는 건드리지 않는다.

Usage: python streaming/producer.py
"""
import json
from pathlib import Path

import pandas as pd
from kafka import KafkaProducer

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
TOPIC = "jdf.raw_postings"
BOOTSTRAP_SERVERS = "localhost:9092"


def load_postings():
    frames = [pd.read_parquet(p) for p in sorted(RAW_DIR.glob("*/*.parquet"))]
    return pd.concat(frames, ignore_index=True)


def main():
    df = load_postings()
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False, default=str).encode("utf-8"),
    )

    sent = 0
    for record in df.to_dict(orient="records"):
        producer.send(TOPIC, value=record)
        sent += 1
    producer.flush()
    producer.close()

    print(f"sent={sent} topic={TOPIC}")


if __name__ == "__main__":
    main()
