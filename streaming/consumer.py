"""4차시 과제용 Kafka Consumer.

jdf.raw_postings topic을 처음부터 읽어 data/kafka_landed/postings.jsonl로
적재한다. consumer_timeout_ms로 새 메시지가 없으면 자동 종료(배치 소비).

Usage: python streaming/consumer.py
"""
import json
from pathlib import Path

from kafka import KafkaConsumer

REPO_ROOT = Path(__file__).resolve().parent.parent
LANDED_DIR = REPO_ROOT / "data" / "kafka_landed"
LANDED_FILE = LANDED_DIR / "postings.jsonl"
TOPIC = "jdf.raw_postings"
BOOTSTRAP_SERVERS = "localhost:9092"


def main():
    LANDED_DIR.mkdir(parents=True, exist_ok=True)

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        group_id="jdf-consumer-4th",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        consumer_timeout_ms=10_000,  # 10초간 새 메시지 없으면 종료
    )

    received = 0
    with open(LANDED_FILE, "w", encoding="utf-8") as f:
        for msg in consumer:
            f.write(json.dumps(msg.value, ensure_ascii=False) + "\n")
            received += 1
    consumer.close()

    print(f"received={received} saved_to={LANDED_FILE}")


if __name__ == "__main__":
    main()
