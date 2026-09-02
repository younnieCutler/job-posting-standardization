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

## 8. BI 화면 (Streamlit) — 파이프라인 저장 결과 사용

✅ `app/dashboard.py` (`streamlit run app/dashboard.py`, 별도 `.venv-dashboard`).

**한 줄 방어 논리**: 실제 Public ATS 데이터는 **시장 스냅샷 분석**에, 일본어 Synthetic
데이터는 **표준화 파이프라인 품질 검증**에 사용했다. 목적이 달라 화면에서도 분리했고,
합쳐서 하나의 시장 지표로 만들지 않는다.

**첫 화면에서 데이터셋 하나를 고른다** (합치지 않음):

| 데이터셋 | 소스 파일 | 용도 | 허용 표현 |
|---|---|---|---|
| 일본어 표준화 데이터셋 (합성) | `data/processed/postings_clean.parquet` | 표기 흔들림을 얼마나 일관되게 정리했는지 검증 | "표준화했을 때 이렇게 통합된다" |
| 글로벌 공개 ATS 데이터셋 (실제, ~2만건) | `data/golden-set/public-it-postings-canonical/dt=<date>/` | 실제 공개 공고 시장 스냅샷 | "이 표본에서는 Python 관련 공고가 N건 관측됐다" |

**공통 원칙**:
- 개발자용 컬럼명·DB 용어(`job_family_group`, `NFKC`, `parquet`, `mart`, `taxonomy` 등)를 화면에
  노출하지 않는다. 사용자 언어로 먼저 표시하고, 기술 설명은 캡션/도움말에서만.
- 차트 제목은 질문형 ("채용공고는 어떤 채널에서 많이 수집됐나?").
- 각 섹션 상단에 "이 화면을 보는 사람" + "이 화면으로 답하려는 질문" 한 줄 (Revelio 방식).
- 미구현(직무 분류, 연봉 파싱, 클라우드 저장/집계 테이블, 채용률·이탈률·경쟁률·실제 급여 벤치마크)은
  완성 기능으로 표시하지 않고 Methodology 섹션에 "아직 만들지 않은 것"으로 명시.

**일본어 트랙 흐름**: 요약(무엇이 들어 있나) → 직무 수요 → 스킬 신호 → 채널 → 표준화 품질
(측정 가능한 지표만: 전체 공고 수, 표기 통일로 직무명 바뀐 수, 중복 제거된 수, 값 비어있는 비율,
연봉 표기 방식 가짓수, 우대요건 항목명 가짓수) → 방법·출처.

**글로벌 ATS 트랙 흐름**: 요약 → 기업(상위) → 직무명(상위) → 근무 지역(상위) → 기술 키워드
(관측됨) + 회사별 기술 → 출처 비교(Greenhouse vs Ashby) → 방법·출처.

언어 전환: 한국어 / 日本語 / English (`app/i18n.py`). 벤치마킹 상세: [`benchmarking.md`](benchmarking.md).

**요청·응답 예시 1개** (제출 시 캡처): 일본어 트랙 "스킬 신호" 섹션 — 직무 분야 필터에서
`data_ai` 선택 → 그 부분집합의 스킬 키워드별 공고 수 (`Python`/`パイソン`/`PYTHON` 표기 변형 합산).
직무 분류 체계가 아니라 표기 변형 병합 키워드 집계임을 캡션에 명시.

🔨 BigQuery/dbt 마트 모드는 마트 구축 후 별도. 현재는 로컬 파일만 사용.
