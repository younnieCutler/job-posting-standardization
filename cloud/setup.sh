#!/usr/bin/env bash
# cloud/setup.sh — GCP 리소스 1회 준비 (멱등)
#
# ⚠️  실제 클라우드 리소스를 만든다. 사용자가 명시적으로 "실행해" 라고
#     지시했을 때만 돌린다. 존재하면 건너뛴다.
#
# 사용: bash cloud/setup.sh
set -euo pipefail

PROJECT="${JDF_GCP_PROJECT:-bright-link-507313-q3}"
REGION="${JDF_GCP_REGION:-asia-northeast1}"
BUCKET="${JDF_GCS_BUCKET:-${PROJECT}-jdf-raw}"
DATASET="${JDF_BQ_DATASET:-jdf}"

echo "project=${PROJECT} region=${REGION} bucket=gs://${BUCKET} dataset=${DATASET}"

echo "▶ API 활성화"
gcloud services enable bigquery.googleapis.com storage.googleapis.com \
  --project "${PROJECT}"

echo "▶ GCS 버킷"
if gsutil ls -b "gs://${BUCKET}" >/dev/null 2>&1; then
  echo "  이미 있음 — skip"
else
  gsutil mb -p "${PROJECT}" -l "${REGION}" "gs://${BUCKET}"
  echo "  생성됨"
fi

echo "▶ BigQuery 데이터셋"
if bq --project_id="${PROJECT}" ls -d 2>/dev/null | grep -qw "${DATASET}"; then
  echo "  이미 있음 — skip"
else
  bq --location="${REGION}" --project_id="${PROJECT}" mk -d "${DATASET}"
  echo "  생성됨"
fi

echo "완료. 다음: scripts/run_pipeline.sh --cloud"
