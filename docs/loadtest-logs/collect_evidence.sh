#!/bin/bash
# 5차시 과제 증거 수집 — 각 실험 dt 파티션에서 manifest.json + CSV 5줄 샘플을 뽑아
# docs/loadtest-logs/sample-output/에 저장 (전체 파티션은 gitignore 대상, 샘플만 커밋).
set -euo pipefail
cd "$(dirname "$0")/../.."

collect() {
  local dt="$1" label="$2"
  local src="data/golden-set/public-it-postings/dt=${dt}"
  local dst="docs/loadtest-logs/sample-output/${label}-dt=${dt}"
  mkdir -p "$dst"
  cp "$src/manifest.json" "$dst/manifest.json"
  head -n 6 "$src/postings.csv" > "$dst/postings-sample.csv"
  echo "collected: $dst"
}

collect "2026-08-30-baseline" "1-baseline"
collect "2026-08-30-scaleup" "2-scaleup"
collect "2026-08-30-dup" "3-duplicate"
collect "2026-08-30-interrupt-test" "5-interrupt-test"
