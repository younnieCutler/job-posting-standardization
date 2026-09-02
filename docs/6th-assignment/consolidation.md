# 6차시 과제 제출 본문 — 부하·복구 보완 + 전체 흐름 점검

작성 2026-09-01 · 갱신 2026-09-02
쉬운 말 결정 배경: [`decisions.md`](decisions.md) · 리얼리티 설계: [`realism-design.md`](realism-design.md) ·
단계별 건수: [`stage-counts.md`](stage-counts.md) · 벤치마킹: [`benchmarking.md`](benchmarking.md)

## 이번 라운드에서 실제로 한 것 / 안 한 것

| 항목 | 상태 |
|---|---|
| Streamlit 표준화 리포트 (2 데이터셋 분리, 3개 언어) | ✅ `app/dashboard.py` |
| 벤치마킹 분석 (Lightcast/HRog/Revelio/TheirStack) | ✅ `benchmarking.md` |
| 로컬 파이프라인 단계별 건수 정리 | ✅ `stage-counts.md` |
| README에 리포트 실행법·목적 | ✅ |
| GCS 업로드 · BigQuery 적재 · `MERGE` · dbt 마트 | ⏳ 미착수 (다음 라운드) |
| Airflow 클라우드 태스크 · `on_failure_callback` alert | ⏳ 미착수 |
| 합성 데이터 리얼리티 강화 (job tag, 템플릿, 볼륨) | ⏳ 미착수 |
| 구성도(다이어그램) 갱신 | ⏳ 미착수 |

즉 6차시는 **"파이프라인이 최종 결과(BI 리포트)까지 이어지는지"를 로컬 범위에서 점검**하고,
클라우드 이전은 다음 라운드로 넘겼다. 아래는 그 로컬 범위 점검 결과다.

---

## 1. 기준 실행 vs 부하 실행 비교

### 1-A. 실제 공개 ATS 트랙 — 5차시 결과 인용 ✅

전문: [`docs/loadtest-logs/evidence.md`](../loadtest-logs/evidence.md)

| 실험 | 입력 | collect 시간 | 수집 건수 | normalize 시간 | Spark 전/후 | 오류·미처리 |
|---|---|---|---|---|---|---|
| 베이스라인 | companies=5, limit=20 | 3m26s | 20건 | 6.8s | 20 → 20 | failures=5 (대상 회사에 공개 보드 없음) |
| 부하 증가 | companies=300 | 3m19s | 25,684건 | 8.3s | 25,684 → 25,684 | failures=5 |

핵심: 건수 1,284배 증가에도 collect 시간 거의 불변(카탈로그 전체 순회가 병목). normalize는
데이터량이 시간에 직접 반영(6.8→8.3s). canonical 저장분 재확인: `dt=2026-08-30-scaleup`
25,684행(greenhouse 22,110 / ashby 3,574), `posting_id` 중복 0.

### 1-B. 합성 일본어 트랙 — 로컬 파이프라인 (재확인) ✅ / 클라우드 적재 ⏳

| 단계 | 값 (2026-08-23 생성 스냅샷 기준) |
|---|---|
| 생성 (`generate_synthetic_postings.py`, N_ROLES=160) | 590건, 7채널 (`data/raw/<platform>/*.parquet`) |
| Kafka Producer 전송 / Consumer 수신 | 590 / 590 |
| Spark 전처리 전 / 후 | 590 → 575 (negative_control 15건 제외, `posting_id` 중복 0) |
| GCS 업로드 · BigQuery staging · `MERGE` · dbt 마트 | ⏳ 미착수 |

기준/부하 두 조건으로 나눈 재실행은 이 트랙에선 5차시에 ATS 트랙으로 이미 검증했고
(1-A), 6차시엔 합성 트랙을 새로 부하 실행하지 않았다. 볼륨 확대(`N_ROLES` 상향)는
다음 라운드 "리얼리티 강화"에 포함.

---

## 2. 실패한 단계 / 재실행 위치 / 재실행 후 저장 결과

### 2-A. 5차시 장애 3종 — 인용 ✅

| 장애 | 재현 방법 | 결과 | 복구 |
|---|---|---|---|
| 중복 실행 | 같은 `dt=` 파티션으로 collect→normalize 2회 | 40건 누적 안 됨, 20건 유지 | 불필요 (덮어쓰기가 멱등 보장) |
| 잘못된 입력 | 존재하지 않는 catalog-url | `HTTPError 404` 즉시 실패, 부분 파일 없음 | catalog-url 고쳐 재실행 |
| 강제 중단 | Spark 정규화 중 `timeout 3`으로 kill | 출력 0개 (원자적 쓰기라 깨진 parquet 없음) | 같은 명령 1회 재실행 → 25,684 완전 복구 |

재실행 위치: 실패한 태스크만 (`collect` 또는 `spark_normalize_public_postings.py`).
재실행 후 저장 결과: 원본 건수 그대로, 유실·중복 없음.

### 2-B. BigQuery `MERGE` 재실행 멱등성 ⏳

BigQuery 적재를 이번 라운드에 하지 않아 측정 불가. 다음 라운드에 `load_to_bq.py`를
같은 `run_date`로 2회 실행 → `canonical_total` 불변 확인 예정. 5차시에서 남긴
"덮어쓰기 기반 안전성 → `MERGE ON posting_id` 누적 기반 안전성" 전환은 그때 이행.

---

## 3. fallback / alert 실제 동작

### 3-A. fallback ✅ (구현됨, 문서화)

- `collect_public_ats_postings.py`가 개별 회사 API 실패를 `manifest.json`의 `failures=N`에
  기록하고 **계속 진행** (전체 중단 아님).
- 5차시 부하 로그에서 `failures=5`로 실제 동작 확인 — 부분 실패를 흡수하고 20~25,684건을 저장.

### 3-B. alert ⏳

Airflow `on_failure_callback` 기반 알림은 이번 라운드에 구현하지 않았다. 다음 라운드에
`load_to_bq.py`의 빈 입력 가드(`staging_rows == 0` → raise) + 콜백으로 알림 파일 생성,
빈 파티션 1회 실행해 증빙 캡처 예정.

---

## 4. 최신 구성도 + 데이터 모델

- **구성도**: `docs/diagrams/architecture-diagram-v1.html` 갱신 ⏳ (클라우드 꼬리 미구현이라 보류).
  현재 유효한 그림은 README mermaid — 로컬 에뮬레이션 기준.
- **데이터 모델** (리포트가 읽는 두 저장 결과):

| 데이터셋 | 파일 | 주요 컬럼 |
|---|---|---|
| 합성 일본어 | `data/processed/postings_clean.parquet` | `posting_id`, `source_platform`, `company_name`, `raw_title` / `raw_title_normalized`, `job_family_group`, `tier`, `salary_min`/`salary_max`/`salary_text`/`salary_type`, `location`/`location_raw`, `preferred_raw`/`requirements_raw`/`description_raw`, `tier_blended`, `coverage_gap_applied` |
| 실제 공개 ATS | `data/golden-set/public-it-postings-canonical/dt=<date>/` | `posting_id`, `source_platform`(greenhouse/ashby), `company_name`, `title` / `title_normalized`, `location`, `department`, `description` / `description_normalized`, `source_url`, `collected_at` |

`posting_id` = `sha256(source_platform + source_posting_id)` (두 트랙 공통, 결정적 해시).

---

## 5. Kafka·Spark·저장·Airflow 단계별 처리 건수 + 확인 방법

상세: [`stage-counts.md`](stage-counts.md). 요약:

| 단계 | 도구 | 확인 방법 |
|---|---|---|
| 합성 생성 | `generate_synthetic_postings.py` | stdout `postings=N`, `data/raw/<platform>/*.parquet` 행 수 합 = 590 |
| 스트리밍 | Kafka Producer/Consumer | `data/kafka_landed/postings.jsonl` 줄 수 |
| 전처리 | Spark (`spark_preprocess.py`) | stdout `before=590 after=575`, `data/processed/postings_clean.parquet` |
| ATS 수집 | `collect_public_ats_postings.py` | `manifest.json`의 `records` / `failures` |
| ATS 정규화 | Spark (`spark_normalize_public_postings.py`) | stdout `before=N after=N`, `dt=<date>/*.parquet` |
| 오케스트레이션 | Airflow (`collect_public_postings` DAG) | `docs/airflow-run-logs/`, `airflow dags test` 로그 |
| 리포트 | Streamlit (`app/dashboard.py`) | 화면 KPI = parquet 집계값 (자체검증 `python app/test_dashboard.py`) |

---

## 6. 아직 실행되지 않는 단계 / 남은 작업

- GCS 업로드 · BigQuery staging + `MERGE` · dbt 마트(`stg_postings`, `mart_*`) · `dbt test`
- Airflow 클라우드 태스크(`push_to_cloud`) · `on_failure_callback` alert · 크론 스케줄 등록
- 합성 데이터 리얼리티 강화: 厚労省 job tag(분포) · 문장 템플릿 풀(구조) · 볼륨 확대
- Canonical Schema 전체 매핑: 급여 텍스트 파서 · 직무 taxonomy 매핑 · 등급 정규화
- 구성도(다이어그램) 클라우드 꼬리 반영
- 동시성 경합 실험 · Kafka 스트리밍 트랙 장애 재현

---

## 7. README

✅ `README.md`에 "6차시 과제 — 표준화 리포트 (Streamlit)" 섹션 추가:
실행법(`streamlit run app/dashboard.py`), 두 데이터셋 분리 표, 화면 원칙, 두 트랙 흐름,
자체검증 명령. `README.ja.md` 반영 ⏳.

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
| 글로벌 공개 ATS 데이터셋 (실제, ~2.5만건) | `data/golden-set/public-it-postings-canonical/dt=<date>/` | 실제 공개 공고 시장 스냅샷 | "이 표본에서는 Python 관련 공고가 N건 관측됐다" |

**공통 원칙**:
- 개발자용 컬럼명·DB 용어(`job_family_group`, `NFKC`, `parquet`, `mart`, `taxonomy` 등)를 화면에
  노출하지 않는다. 사용자 언어로 먼저 표시하고, 기술 설명은 캡션/도움말에서만.
- 차트 제목은 질문형 ("채용공고는 어떤 채널에서 많이 수집됐나?").
- 각 섹션 상단에 "이 화면을 보는 사람" + "이 화면으로 답하려는 질문" 한 줄 (Revelio 방식).
- 미구현(직무 분류, 연봉 파싱, 클라우드 저장/집계 테이블, 채용률·이탈률·경쟁률·실제 급여 벤치마크)은
  완성 기능으로 표시하지 않고 "아직 만들지 않은 것"으로 명시.

**일본어 트랙 흐름**: 요약(무엇이 들어 있나) → 직무 수요 → 스킬 신호 → 채널 → 표준화 품질
(측정 가능한 지표만) → 방법·출처.
측정 가능한 지표 실측 (2026-08-23 스냅샷, 575건):

| 지표 | 값 |
|---|---|
| 전체 공고 수 | 575 |
| 표기 통일로 직무명이 바뀐 공고 수 | 0 (이 스냅샷 직무명은 이미 정규 형태) |
| 중복으로 제거된 공고 수 | 0 (`posting_id` 중복 없음) |
| 연봉 표기 방식 가짓수 | 4 (`月給制` 204 / `年俸制` 179 / `月給+賞与制` 175 / 빈값 17) — 아직 파싱 전 |
| '우대요건' 항목명 가짓수 | 3 (`歓迎要件` / `尚可条件` / `求める経験・スキル`) — 아직 공통명 미기록 |
| 값이 비어 있는 비율 상위 | `agency` 78% · `posted_at` 52% · `salary_min`/`salary_max` 3% |

**글로벌 ATS 트랙 흐름**: 요약 → 기업(상위) → 직무명(상위) → 근무 지역(상위) → 기술 키워드
(관측됨) + 회사별 기술 → 출처 비교(Greenhouse vs Ashby) → 방법·출처.
`dt=2026-08-30-scaleup` 기준: 25,684건 · 300개사 · 2개 출처(greenhouse 22,110 / ashby 3,574).

언어 전환: 한국어 / 日本語 / English (`app/i18n.py`).

**요청·응답 예시 1개** (제출 시 캡처): 일본어 트랙 "스킬 신호" 섹션 — 직무 분야 필터에서
`data_ai` 선택 → 그 부분집합의 스킬 키워드별 공고 수 (`Python`/`パイソン`/`PYTHON` 표기 변형 합산).
직무 분류 체계가 아니라 표기 변형 병합 키워드 집계임을 캡션에 명시.

⏳ BigQuery/dbt 마트 모드는 마트 구축 후 별도. 현재는 로컬 파일만 사용.
