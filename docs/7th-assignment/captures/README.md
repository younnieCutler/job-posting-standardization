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
| 07 | `cloud/setup.sh` 출력 | .txt |
| 08 | `cloud/load_to_bq.py` 출력 (staging/updated/inserted/canonical_total) | .txt |
| 09 | MERGE 멱등성 — load_to_bq 2회 → canonical_total 불변 | .txt |
| 10 | `bq query` canonical COUNT = spark after | .txt |
| 11 | `bq query` canonical 상위 10행 (SQL 조회 장면) | .txt |
| 12 | `dbt run` + `dbt test` 통과 | .txt |
| 13 | `bq query` mart 행수·상위값 | .txt |
| 14 | Streamlit — BQ 마트 읽기 모드 | .png |
| 15 | Airflow `push_to_cloud=true` run — 태스크 success | .txt |
| 16 | alert 실증 — 빈 파티션 → 콜백 JSON | .txt + .json |
| 17 | 5차시 장애 3종 (기존 `docs/loadtest-logs/*.log` 발췌) | .txt |
| 18 | 현재 구현 다이어그램 렌더 | .png |

07~16: `cloud/`·`dbt/`·DAG 코드는 저장소에 있으나 **실제 클라우드 미실행**. 해당 슬라이드는 "코드 있음 · 미실행"으로 표시. 실행은 사용자 지시 시.
