#!/usr/bin/env bash
# 7차시 — 합성 트랙 원샷 실행. 입력 → 처리 → 저장 → 읽기를 한 번의 실행으로 재현한다.
#
#   generate_synthetic_postings.py  ->  data/raw/<platform>/*.parquet
#   -> Kafka (producer -> topic jdf.raw_postings -> consumer)  -> data/kafka_landed/postings.jsonl
#   -> spark_preprocess.py (NFKC + dedup + negative_control 제외)  -> data/processed/postings_clean.parquet
#   -> read (scripts/read_result.py)  -> 요약 출력
#
# 멱등: SEED=42 고정, 모든 출력은 overwrite. 매 실행 Kafka 토픽을 새로 만들어 누적을 막는다.
# 실패해도 되돌릴 수 있음(로컬 파일만 덮어씀). 외부 API 호출 없음.
#
# 사용법:
#   scripts/run_pipeline.sh            # 로컬 합성 트랙만
#   scripts/run_pipeline.sh --cloud    # + GCS 업로드 + BigQuery MERGE (cloud/ 스크립트, 사전 인증 필요)
#   scripts/run_pipeline.sh --help
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PY="${PYTHON:-python3}"
RUN_CLOUD=0
RUN_DATE="$(date -u +%F)"

for arg in "$@"; do
  case "$arg" in
    --cloud) RUN_CLOUD=1 ;;
    --help|-h)
      sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "unknown arg: $arg (try --help)" >&2; exit 2 ;;
  esac
done

line() { printf '%s\n' "------------------------------------------------------------"; }
step() { line; printf '▶ %s\n' "$1"; line; }

# ---------- 0. Kafka 준비 (토픽 초기화) ----------
step "0/6  Kafka 기동 (토픽 초기화)"
if ! docker info >/dev/null 2>&1; then
  echo "Docker 데몬이 꺼져 있습니다. Docker Desktop / OrbStack을 먼저 켜고 다시 실행하세요." >&2
  exit 1
fi
docker compose down >/dev/null 2>&1 || true
docker compose up -d
printf 'Kafka(9092) 대기'
for _ in $(seq 1 30); do
  if nc -z localhost 9092 >/dev/null 2>&1; then echo " → up"; break; fi
  printf '.'; sleep 1
done
nc -z localhost 9092 >/dev/null 2>&1 || { echo; echo "Kafka가 30초 안에 올라오지 않았습니다." >&2; exit 1; }
sleep 2  # broker 안정화

# ---------- 1. 생성 ----------
step "1/6  합성 공고 생성  (ingestion/generate_synthetic_postings.py)"
GEN_OUT="$($PY ingestion/generate_synthetic_postings.py)"
echo "$GEN_OUT"
GENERATED="$(echo "$GEN_OUT" | sed -n 's/.*postings=\([0-9]*\).*/\1/p' | head -1)"

# ---------- 2. Producer ----------
step "2/6  Kafka Producer  (streaming/producer.py)"
PROD_OUT="$($PY streaming/producer.py)"; echo "$PROD_OUT"
SENT="$(echo "$PROD_OUT" | sed -n 's/.*sent=\([0-9]*\).*/\1/p' | head -1)"

# ---------- 3. Consumer ----------
step "3/6  Kafka Consumer  (streaming/consumer.py)"
CONS_OUT="$($PY streaming/consumer.py)"; echo "$CONS_OUT"
RECEIVED="$(echo "$CONS_OUT" | sed -n 's/.*received=\([0-9]*\).*/\1/p' | head -1)"

# ---------- 4. Spark 전처리 ----------
step "4/6  Spark 전처리  (streaming/spark_preprocess.py)"
SPARK_OUT="$($PY streaming/spark_preprocess.py)"; echo "$SPARK_OUT"
BEFORE="$(echo "$SPARK_OUT" | sed -n 's/.*before=\([0-9]*\).*/\1/p' | head -1)"
AFTER="$(echo "$SPARK_OUT"  | sed -n 's/.*after=\([0-9]*\).*/\1/p'  | head -1)"

# ---------- 5. 클라우드 (선택) ----------
CANONICAL="—"
if [ "$RUN_CLOUD" -eq 1 ]; then
  step "5/6  클라우드 적재  (cloud/upload_to_gcs.py → cloud/load_to_bq.py)"
  $PY cloud/upload_to_gcs.py --run-date "$RUN_DATE"
  LOAD_OUT="$($PY cloud/load_to_bq.py --run-date "$RUN_DATE")"; echo "$LOAD_OUT"
  CANONICAL="$(echo "$LOAD_OUT" | sed -n 's/.*canonical_total=\([0-9]*\).*/\1/p' | head -1)"
else
  step "5/6  클라우드 적재  (건너뜀 — --cloud 로 켜기)"
fi

# ---------- 6. 읽기 ----------
step "6/6  저장 결과 읽기  (scripts/read_result.py)"
$PY scripts/read_result.py

# ---------- 단계별 건수 표 ----------
line
echo "단계별 처리 건수"
line
printf '%-32s %s\n' "1. 생성 (data/raw/*.parquet)"          "${GENERATED:-?}"
printf '%-32s %s\n' "2. Kafka Producer 전송"                 "${SENT:-?}"
printf '%-32s %s\n' "3. Kafka Consumer 수신"                 "${RECEIVED:-?}"
printf '%-32s %s\n' "4. Spark 전처리 전"                     "${BEFORE:-?}"
printf '%-32s %s\n' "5. Spark 전처리 후 (최종 저장)"         "${AFTER:-?}"
if [ "$RUN_CLOUD" -eq 1 ]; then
printf '%-32s %s\n' "6. BigQuery canonical 총계"             "${CANONICAL:-?}"
fi
line
echo "최종 저장: data/processed/postings_clean.parquet"
echo "다음: streamlit run app/dashboard.py   (별도 venv: .venv-dashboard)"
