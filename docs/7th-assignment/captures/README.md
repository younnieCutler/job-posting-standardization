# 7차시 증빙 캡처

발표 자료·README "확인 방법"에 embed 하는 실행 증빙. 파일명 `NN-<주제>.png` / `.txt`.

| # | 대상 | 형식 |
|---|---|---|
| 01 | `scripts/run_pipeline.sh` 단계별 건수 표 | .txt ✅ (01, 01b 2회분 — 멱등 확인) |
| 02 | `python app/test_dashboard.py` 통과 | .txt ✅ |
| 03 | Streamlit — 일본어 트랙 요약 + 표준화 품질 | .png |
| 04 | Streamlit — 스킬 신호, `data_ai` 필터 (요청·응답 예시) | .png |
| 05 | Streamlit — 글로벌 ATS 트랙 | .png |
| 06 | ATS Airflow run 로그 (collect→normalize) | .txt |
| 07 | `cloud/setup.sh` 출력 | .txt ✅ (버킷+데이터셋 생성) |
| 08 | `run_pipeline.sh --cloud` 전체 (upload + load_to_bq: staging 575 / inserted 575 / canonical_total 575) | .txt ✅ |
| 09 | MERGE 멱등성 — 2회차 updated=575 inserted=0 canonical_total=575 (불변) | .txt ✅ |
| 10 | `cloud/query_marts.py` — canonical COUNT=575 (=spark after) + 상위 10행 + 마트 | .txt ✅ |
| 11 | (10에 포함) canonical 상위 10행 = SQL 조회 서빙 장면 | .txt ✅ |
| 12 | `dbt run` PASS=3 + `dbt test` PASS=7 | .txt ✅ |
| 13 | (10에 포함) mart_tech_demand 7행 / mart_platform_dist 7행 | .txt ✅ |
| 14 | Streamlit — BQ 마트 읽기 모드 | .png |
| 15 | Airflow `push_to_cloud=true` run — 태스크 success | .txt |
| 16 | alert 가드 — 빈 파티션(0행) → `staging_rows==0` → raise, MERGE 중단 | .txt ✅ |
| 17 | 5차시 장애 3종 (기존 `docs/loadtest-logs/*.log` 발췌) | .txt |
| 18 | 현재 구현 다이어그램 렌더 | .png |

## 상태 (2026-09-07)

- **확보 (.txt)**: 01·01b·02·07·08·09·10·11·12·13·16 — 로컬 원샷 + 클라우드 GCS→BQ MERGE→dbt 실행 결과
- **미확보 (사용자가 aside로 캡처 예정)**:
  - 03·04·05 — Streamlit 스크린샷 (`.venv-dashboard/bin/streamlit run app/dashboard.py`)
  - 17 — 5차시 장애 3종 (`docs/loadtest-logs/` 에서 발췌, 파일은 이미 있음)
  - 18 — `docs/diagrams/architecture-diagram-v1.html` mermaid 렌더 PNG
  - 06·15 — Airflow run (선택). 15는 `push_to_cloud=true` → 이미 만든 canonical/mart 에 MERGE·덮어쓰기 하므로 실행 전 확인
- 14 (Streamlit BQ 마트 읽기 모드) — **미채택**. dashboard 는 로컬 parquet 전용, BQ 서빙은 `cloud/query_marts.py` 로 분리
