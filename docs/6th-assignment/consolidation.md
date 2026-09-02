# 6차시 과제 제출 본문 — 부하·복구 보완 + 전체 흐름 점검

작성 2026-09-01 · 마감 2026-09-03(목) 17:00
쉬운 말 결정 배경은 [`decisions.md`](decisions.md), 리얼리티 설계는 [`realism-design.md`](realism-design.md).

> **상태 표기**: ✅ 완료 인용 / 🔨 이번 라운드 작성 예정 (내일 수치·캡처 채움)

---

## 1. 기준 실행 vs 부하 실행 비교

### 1-A. ATS(영어) 트랙 — 5차시 결과 인용 ✅

전문: [`docs/loadtest-logs/evidence.md`](../loadtest-logs/evidence.md)

| 실험 | 입력 | collect 시간 | 수집 건수 | normalize 시간 | Spark 전/후 | 오류·미처리 |
|---|---|---|---|---|---|---|
| 베이스라인 | companies=5, limit=20 | 3m26s | 20건 | 6.8s | 20 → 20 | failures=5 (대상 회사에 공개 보드 없음) |
| 부하 증가 | companies=300 | 3m19s | 25,684건 | 8.3s | 25,684 → 25,684 | failures=5 |

핵심: 건수 1,284배 증가에도 collect 시간 거의 불변(카탈로그 전체 순회가 병목,
`--companies`는 순회 후 선택에만 영향). normalize는 데이터량이 시간에 직접 반영(6.8→8.3s).

### 1-B. 합성 일본어 트랙 — 6차시 클라우드 적재 🔨

| 단계 | 기준 실행 | 부하 실행 |
|---|---|---|
| 생성 건수 (`N_ROLES` 조정) | 🔨 | 🔨 |
| Kafka Producer 전송 / Consumer 수신 | 🔨 | 🔨 |
| Spark 전처리 전 / 후 | 🔨 | 🔨 |
| GCS 업로드 파일 수 | 🔨 | 🔨 |
| BigQuery staging 로드 건수 | 🔨 | 🔨 |
| MERGE 후 canonical 총계 | 🔨 | 🔨 |
| dbt 마트 행 수 | 🔨 | 🔨 |
| 오류·미처리 (negative_control 제외분 등) | 🔨 | 🔨 |

---

## 2. 실패한 단계 / 재실행 위치 / 재실행 후 저장 결과

### 2-A. 5차시 장애 3종 — 인용 ✅

| 장애 | 재현 방법 | 결과 | 복구 |
|---|---|---|---|
| 중복 실행 | 같은 `dt=` 파티션으로 collect→normalize 2회 | 40건 누적 안 됨, 20건 유지 | 불필요 (덮어쓰기가 멱등 보장) |
| 잘못된 입력 | 존재하지 않는 catalog-url | `HTTPError 404` 즉시 실패, 부분 파일 없음 | catalog-url 고쳐 재실행 |
| 강제 중단 | Spark 정규화 중 `timeout 3`으로 kill | 출력 0개 (원자적 쓰기라 깨진 parquet 없음) | 같은 명령 1회 재실행 → 25,684 완전 복구 |

### 2-B. 6차시 추가 — BigQuery MERGE 재실행 멱등성 🔨

- 재현: 같은 `run_date`로 `load_to_bq.py` 2회 연속
- 기대: `canonical_total` 불변 (matched는 UPDATE, 새 것만 INSERT)
- 실패 시 재실행 위치: `load_to_bq.py` 만 다시 (GCS 업로드는 그대로 재사용)
- 🔨 실제 수치

---

## 3. fallback / alert 실제 동작

### 3-A. fallback ✅ (구현됨, 문서화)

- collector가 개별 소스 API 실패를 `manifest.json`의 `failures=N`에 기록하고 **계속 진행**
- 5차시 부하 로그에서 `failures=5`로 실제 동작 확인 (전체 중단 아님, 부분 실패 흡수)

### 3-B. alert 🔨 (6차시 신규)

- `load_to_bq.py`에 가드: `staging_rows == 0`이면 `raise`
- Airflow DAG `on_failure_callback` → `docs/airflow-run-logs/alerts/<dag_run_id>.json` 생성
- 실증: 빈 `dt=` 파티션으로 1회 실행 → 실패 유발 → 알림 JSON 캡처
- 🔨 캡처 첨부

---

## 4. 최신 구성도 + 데이터 모델

- 구성도: 🔨 `docs/diagrams/architecture-diagram-v1.html` + README mermaid 갱신
  (합성 일본어 트랙 꼬리 GCS→BigQuery→dbt→Looker 실선화, ATS 트랙 별도 표기)
- 데이터 모델: [`docs/plans/2026-09-01-6th-assignment-cloud-bi.md`](../plans/2026-09-01-6th-assignment-cloud-bi.md) §3
  — `jdf.postings_canonical` 컬럼 표 (`posting_id` PK, 원문/정규화/파생 층 구분)

---

## 5. Kafka·Spark·저장·Airflow 단계별 처리 건수 + 확인 방법

🔨 상세: [`stage-counts.md`](stage-counts.md)

| 단계 | 도구 | 확인 방법 |
|---|---|---|
| 생성 | `generate_synthetic_postings.py` | stdout `postings=N`, `data/raw/<platform>/*.parquet` |
| 스트리밍 | Kafka Producer/Consumer | `data/kafka_landed/postings.jsonl` 줄 수 |
| 전처리 | Spark | stdout `before=N after=M`, `data/processed/postings_clean.parquet` |
| 업로드 | `upload_to_gcs.py` | `gsutil ls gs://<bucket>/canonical/dt=<date>/` |
| 적재 | `load_to_bq.py` | stdout `staging_rows/updated/inserted/canonical_total`, `bq query 'SELECT COUNT(*) FROM jdf.postings_canonical'` |
| 변환 | dbt | `dbt run` 로그, `bq query 'SELECT COUNT(*) FROM jdf.mart_tech_demand'` |
| 오케스트레이션 | Airflow | `docs/airflow-run-logs/`, Airflow UI 태스크 상태 |

---

## 6. 아직 실행되지 않는 단계 / 남은 작업

- 리얼리티 2층: JOBSKAPE 오프라인 LLM 문장뱅크
- 데이터 10만건+ 스케일업
- Canonical Schema 전체 매핑: 급여 텍스트 파서 · 직무 taxonomy 전체 매핑 · 등급 정규화
- dbt Conformed Dimension 통합 마트 (공급·수요 갭 분석)
- 크론 스케줄 등록 (현재 수동 트리거·`airflow dags test`만)
- 동시성 경합 실험 (두 프로세스가 같은 `dt=` 파티션 동시 쓰기)
- Kafka 스트리밍 트랙 장애 재현 (4차시 제출분)

---

## 7. README

🔨 `README.md` + `README.ja.md`에 "6차시 — 클라우드 추가 트랙 + dbt + BI" 섹션.
로컬 실행법은 유지, 클라우드 실행법(`cloud/setup.sh` → DAG `push_to_cloud` → Looker 연결) 추가.

---

## 8. BI 화면 + 예시 1개

🔨 Streamlit 대시보드(`app/dashboard.py`, `streamlit run`) 스크린샷 + `mart_tech_demand` 쿼리 결과 1개
(요청: "기술별 공고 수" → 응답: 표기 변형 합쳐진 후 canonical 스킬별 건수).
BQ 마트를 직접 쿼리 → 파이프라인 저장 결과를 실제로 쓰는 화면. Looker Studio는 다음 라운드 후보.
