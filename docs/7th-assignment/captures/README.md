# 7차시 증빙 캡처

발표 자료·README "확인 방법"에 embed 하는 실행 증빙. 파일명 `NN-<주제>.png` / `.txt`.

| # | 대상 | 형식 |
|---|---|---|
| 01 | `scripts/run_pipeline.sh` 단계별 건수 표 | .txt ✅ (01, 01b 2회분 — 멱등 확인) |
| 02 | `python app/test_dashboard.py` 통과 | .txt ✅ |
| 03 | Streamlit — 일본어 트랙 요약 KPI(575/165/7/6) + 직무 수요 | .png ✅ |
| 04 | Streamlit — 스킬 신호, `data_ai` 필터 적용 (AWS/SQL/요건정의) | .png ✅ |
| 05 | Streamlit — 글로벌 ATS 트랙 KPI(25,684/300/2) + 기업 상위 | .png ✅ |
| 06 | ATS Airflow run 로그 (collect→normalize) | .txt |
| 07 | `cloud/setup.sh` 출력 | .txt ✅ (버킷+데이터셋 생성) |
| 08 | `run_pipeline.sh --cloud` 전체 (upload + load_to_bq: staging 575 / inserted 575 / canonical_total 575) | .txt ✅ |
| 09 | MERGE 멱등성 — 2회차 updated=575 inserted=0 canonical_total=575 (불변) | .txt ✅ |
| 10 | `cloud/query_marts.py` — canonical COUNT=575 (=spark after) + 상위 10행 + 마트 | .txt ✅ |
| 11 | BigQuery 콘솔 SQL 에디터 + 결과 그리드 (mart_tech_demand 7행) | .png ✅ · (10 .txt에도 포함) |
| 12 | `dbt run` PASS=3 + `dbt test` PASS=7 | .txt ✅ |
| 13 | (10에 포함) mart_tech_demand 7행 / mart_platform_dist 7행 | .txt ✅ |
| 14 | Looker Studio — BigQuery dbt 마트 리포트 (스코어카드 + 직무×경력 + 스킬 수요). [링크](https://datastudio.google.com/reporting/a69e9404-fea5-44cd-ac55-efc26c06720c) | .png ✅ |
| 15 | Airflow `push_to_cloud=true` run — 태스크 success | .txt |
| 16 | alert 가드 — 빈 파티션(0행) → `staging_rows==0` → raise, MERGE 중단 | .txt ✅ |
| 17 | 5차시 장애 3종 (중복실행/404/강제중단→복구) 로그 발췌 | .txt ✅ |
| 18 | 현재 구현 다이어그램 mermaid 렌더 | .png ✅ |

## 상태 (2026-09-07)

- **확보**: 01·01b·02 (.txt) · 03·04·05 (.png Streamlit) · 07·08·09·10·12·13·16 (.txt 클라우드) · 11 (.png BQ 콘솔) · 17 (.txt 장애 3종) · 18 (.png 다이어그램)
- **미확보 (선택)**: 06·15 — Airflow run. 15는 `push_to_cloud=true` → 이미 만든 canonical/mart 에 MERGE·덮어쓰기 하므로 실행 전 확인 필요
- **미확보 (선택)**: 06 — ATS Airflow run. 15 — Airflow `push_to_cloud` run (기존 canonical/mart 덮어씀, 실행 전 확인)
- Streamlit BQ 마트 읽기 모드는 미채택 (dashboard 로컬 parquet 전용). BQ 서빙 = `cloud/query_marts.py` + BQ 콘솔(11) + **Looker Studio(14)**
