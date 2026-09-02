# 6차시 과제 — 클라우드 추가 트랙 + dbt + BI + 전체 흐름 점검

- 작성: 2026-09-01 (화)
- 마감: 2026-09-03 (목) 17:00
- 마이그레이션 실작업: 2026-09-02 (수)
- 제출: GitHub 링크를 디스코드 #6차시 채널에 공유
- 대상 repo: `job-posting-standardization` (제출 repo)
- 설계 참조: `~/dev/career/job-data-foundry/docs/` (설계 워크스페이스, remote 없음 — §2에서 확인 완료)

---

## 0. 6차시 과제가 요구하는 것

6차시 수업에서 5차시(부하·복구) 제출을 리뷰했고, 그 보완 + 파이프라인이 최종 결과(BI)까지
이어지는지 점검이 이번 과제. **필수 7항목**:

1. 기준 실행 vs 부하 실행 비교 (입력 건수 / 실행시간·처리량 / 최종 저장 건수 / 오류·미처리 건수)
2. 실패한 단계, 재실행 위치, 재실행 후 저장 결과
3. fallback 또는 alert가 실제로 동작한 결과
4. 최신 구성도와 데이터 모델
5. Kafka·Spark·저장·Airflow 실행 화면/로그 + 단계별 처리 건수 + 최종 결과 확인 방법
6. 아직 실행되지 않는 단계와 남은 작업
7. 현재 실행 방법과 확인 결과를 반영한 README

BI를 추가하므로: 저장 결과를 실제로 쓰는 화면 + 요청·응답/예측 예시 1개도 제출.
이미 제출한 5차시 실험은 재실행하지 않음 — 수업 지적 누락·설명부족만 보완.

---

## 1. 이번 라운드 결정 요약 (쉬운 말)

> 상세 근거는 `docs/6th-assignment/decisions.md`. 이 표는 한눈에 보는 용도.

| 무엇을 | 어떻게 정했나 | 왜 |
|---|---|---|
| 어느 데이터 트랙을 클라우드로? | **합성 일본어 트랙** (`ingestion/generate_synthetic_postings.py` → `data/raw/<platform>` → Kafka+Spark → `data/processed`) | README 메인 아키텍처가 이 트랙. 表記ゆれ 정량화(프로젝트 핵심 가치)가 일본어 데이터라야 살아남. ATS(영어) 트랙은 5차시 부하·복구 검증만 담당하고 결과 그대로 인용 |
| 데이터 웨어하우스 | **BigQuery** (ADR-003, 2026-08-18 기확정) | 6차시는 확정이 아니라 **첫 실제 구현**. 설계 workspace ADR 사본은 구버전이라 "미결정"으로 보이나 정본(제출 repo)은 확정 |
| BI 도구 | **제출용 Streamlit** (`app/dashboard.py`), Looker는 다음 라운드 후보 | Looker 수작업·비재현. Streamlit은 코드 커밋 → 재현 가능 = 더 나은 증빙. 지문이 "Streamlit 데이터 연결" 참고자료 명시 |
| dbt | **넣음** (staging 1 + mart 2 + `dbt test`) | 거버넌스 축 증빙(ADR-002). `BashOperator`로 실행(ADR-004). Cosmos는 v2 |
| 재실행 안전성 모델 | 로컬 = 파티션 **덮어쓰기** 유지 / 클라우드 = **`MERGE ON posting_id`** | 5차시 미해결 항목("MERGE 가면 덮어쓰기 안전성이 누적 안전성으로 바뀌어야")의 실제 이행 |
| 합성 데이터 리얼리티 | **4층 스택** (§4). 이번엔 1·3층 + 기존 4층, 2층은 다음 단계 | 건수보다 리얼리티 우선(사용자 지시). LLM 문장뱅크는 하루+ 걸려 마감 밖 |
| 데이터 건수 | 이번 5,000~15,000, 10만+는 차차 | 볼륨은 상수 1줄. 리얼리티가 본질 |
| 로컬 우선 | `docker compose up` / 로컬 parquet가 여전히 기본. 클라우드는 DAG 플래그 `push_to_cloud`로 on/off | ADR-002 "완전 로컬 재현" 보존 |

### 의도적 제외 (→ §6 "남은 작업")
- dbt Conformed Dimension 통합 마트 (v2)
- Canonical Schema 전체 매핑 (급여 파싱·Taxonomy·tier 정규화)
- Kafka 스트리밍 트랙 장애 재현 (4차시 제출분)
- Private/PII 파이프라인 (별 도메인, 공개 공고엔 PII 없음)
- 동시성 경합(race condition) 실험 (5차시 미해결)
- 리얼리티 2층: JOBSKAPE 오프라인 LLM 문장뱅크

---

## 2. 단계 0 확인 결과 — ADR 상태

**정본 = 제출 repo `docs/architecture_decision_record.md`.** 설계 workspace
(`~/dev/career/job-data-foundry/docs/`)의 ADR 사본은 구버전 (PII 서사 잔존, ADR-003
"미결정"으로 표기) — 무시.

| 항목 | 정본(제출 repo) 상태 | 6차시 처리 |
|---|---|---|
| ADR-003 DWH (Snowflake vs BigQuery) | **BigQuery 확정 (2026-08-18)**. `MERGE` idempotency도 BigQuery 기준 설계됨 | 확정된 결정의 **첫 실제 구현** |
| BI 도구 (Streamlit/Looker/Retool) | ADR에 전용 항목 없음 — Looker는 BigQuery 근거로만 언급, 정식 선택 안 됨 = **진짜 미정** | → 제출용 **Streamlit** 부분 확정, Looker 다음 라운드 후보 |
| dbt Core (ADR-002) | 확정 (거버넌스 축) | 유지, 이번에 도입 |
| dbt 실행 방식 (ADR-004) | `BashOperator` (Cosmos는 v2) | 이 방식 |
| Conformed Dimension 마트 | v2 연기 | 제외 |

ADR 문서는 실제 진행보다 뒤처지는 경우가 잦음 — 결정 상태 확인은 README + decisions.md +
memory 를 우선으로.

---

## 3. 데이터 모델

합성 일본어 트랙 → BigQuery `jdf.postings_canonical` (MERGE 대상, `posting_id` PK).
소스 스키마 근거: `data/processed/postings_clean.parquet` 현재 컬럼.

| 컬럼 | 타입 | 층 | 비고 |
|---|---|---|---|
| `posting_id` | STRING | 키 | `sha256(source_platform + source_posting_id)` |
| `role_id` | STRING | 원문 | 같은 자리의 서로 다른 게시(엔티티 해소 정답 연결) |
| `source_platform` | STRING | 원문 | hrmos/doda/geekly/openwork/mid_tenshoku/talentio/company_site |
| `source_posting_id` | STRING | 원문 | |
| `agency` | STRING | 원문 | |
| `company_name` | STRING | 원문 | canonical 회사명은 백로그 |
| `raw_title` | STRING | 원문 | 절대 안 건드림 |
| `raw_title_normalized` | STRING | 정규화 | NFKC |
| `description_raw` / `requirements_raw` / `preferred_raw` | STRING | 원문 | JD 본문 3섹션 |
| `location` / `location_raw` | STRING | 정규화 / 원문 | |
| `salary_min` / `salary_max` | INT64 | 파생 | `salary_text` 파싱 결과 (이번엔 생성기 제공값 그대로, 파서는 백로그) |
| `salary_text` / `salary_type` | STRING | 원문 | 3포맷 (年俸制/月給+賞与/月給制) |
| `tier` | STRING | 파생 | junior/mid/expert (+ null/unknown 예외) |
| `job_family_group` | STRING | 파생 | 영어 코드 (software_development 등 6종) |
| `tier_blended` / `coverage_gap_applied` / `is_negative_control` | BOOL | 메타 | 합성 패턴 플래그 |
| `posted_at` | STRING | 원문 | 있으면 저장, 없으면 null |
| `run_date` | STRING | 파생 | `dt=` 파티션 값 |

---

## 4. 합성 데이터 리얼리티 — 4층 스택

각 층이 다른 종류의 리얼리티를 담당. 이번 라운드는 **1층 + 3층 + (기존)4층**, 2층은 §6.

### 1층 · 분포 리얼리티 — 厚労省 job tag (O-NET 일본판) [이번]
- 소스: https://shigoto.mhlw.go.jp/User/download — 500+ 직업의 職業解説 + 数値情報(태스크, 필요 학력·자격·실무경험, 賃金, 就労者数, 평균연령, スキル・知識 프로파일)
- 이용규약: 편집·가공·재집계 등 2차 이용 명시 허용 (심리검사 문항만 금지)
- 적용: 손으로 적은 `JOB_FAMILY_GROUPS` + 추측한 `SALARY_BANDS_MAN_YEN` → job tag 실측치로 교체. job tag의 職種별 スキル・知識 프로파일 = 실제 스킬 동시출현 → `SKILL_POOL_BY_GROUP` 대체
- **내일 첫 작업: 다운로드 페이지에서 실제 파일 포맷(xlsx/csv) 확인**

### 2층 · 언어 리얼리티 — JOBSKAPE 오프라인 문장뱅크 [다음 단계]
- 참조: JOBSKAPE (arxiv 2402.03242, github magantoine/JobSkape), JobSet (ACM 2024, 10.1145/3672608.3707718)
- 방법: LLM을 **오프라인 1회**만 돌려 (직군 × 스킬조합 × 섹션)별 현실 문장 템플릿 수천 개 뱅크 생성 → 정적 자산으로 커밋 → 런타임은 결정적 슬롯필만. LLM은 자산준비지 파이프라인 런타임 아님 (메모리 결정 "파이프라인 내 LLM 금지" 안 깸)
- 스킬조합 입력: 1층 job tag 스킬 프로파일 재사용
- 작업량 1일+ → 마감 밖. 시간 남으면 소규모 1차 뱅크

### 3층 · 구조 리얼리티 — 템플릿 풀 확장 [이번]
- 섹션별(職務内容/必須要件/歓迎要件/待遇) 골격 30~50개 손작성 + 중첩 슬롯
- 플랫폼별 필드명 변형(`職務内容` vs `仕事内容`), 급여 포맷 차이는 이미 `PLATFORM_PROFILES`에 있음 — 확장만
- 결정적·빠름·무비용. 대시보드·매칭 데모엔 충분

### 4층 · 지저분함 리얼리티 — 골든셋 56행 [기존, 유지]
- `SKILL_VARIANTS`(`Python`/`パイソン`/`PYTHON`), `FIELD_NAME_VARIANTS`, `TIER_BLEND`, `COVERAGE_GAP`
- 이게 정규화 대상 그 자체. 안 건드림

### 볼륨
- `N_ROLES` 상수 조정 (현재 160). 이번 5,000~15,000건 목표면 `N_ROLES` ~2,000~5,000
- `SEED=42` 유지 → 재현 가능. 플랫폼별 parquet write라 메모리 문제 없음
- 느리면 청크 write 또는 Mimesis(Faker 빠른 사촌)로 문자열 생성 교체 — 이번엔 불필요할 듯

---

## 5. 구현 (`cloud/`·`dbt/` 신규, `ingestion/`·로컬 경로 최소 수정)

### 5.1 생성기 (`ingestion/`)
- `synth_rules.py`: job tag 실측 풀로 교체 (직종·급여밴드·스킬 프로파일). `SKILL_VARIANTS` 등 패턴축은 유지
- `synth_templates.py` (신규): 섹션별 문장 골격 풀 30~50개
- `generate_synthetic_postings.py`: 템플릿 풀 참조, `N_ROLES` 상향
- `verify_coverage.py`: 재실행, 축 쏠림 확인 (임계값은 비율 기준이라 그대로)

### 5.2 `cloud/setup.sh`
`gcloud services enable bigquery storage` + 버킷 `gs://<project>-jdf-raw` + BQ 데이터셋 `jdf`. 멱등.

### 5.3 `cloud/upload_to_gcs.py`
`--run-date`. `data/processed/` (또는 canonical parquet) → `gs://<bucket>/canonical/dt=<run-date>/`. 업로드 파일 수 출력.

### 5.4 `cloud/load_to_bq.py`
`--run-date`. GCS parquet → `jdf.staging_postings` (WRITE_TRUNCATE, `run_date` 주입) → `MERGE INTO jdf.postings_canonical USING staging ON posting_id` (matched: UPDATE, not matched: INSERT).
출력: `staging_rows`, `updated`, `inserted`, `canonical_total`.
**alert 가드**: `if staging_rows == 0: raise` — 빈 입력이면 실패시켜 알림 발화.

### 5.5 `dbt/` (dbt Core)
- `models/staging/stg_postings.sql` — canonical에서 타입 캐스팅 + 스킬 태그 정규화(表記ゆれ → canonical tag)
- `models/marts/mart_tech_demand.sql` — canonical 스킬 태그별 공고 수 (표기변형 합쳐진 후)
- `models/marts/mart_platform_dist.sql` — `source_platform`별 건수 + dedup 비율
- `models/marts/schema.yml` — `dbt test`: `posting_id` unique + not_null (거버넌스 증빙)
- `profiles.yml` — BigQuery 타깃, `~/.config/gcloud` ADC 사용

### 5.6 `app/dashboard.py` (Streamlit — 제출용 BI)
- `google-cloud-bigquery` + ADC로 `jdf.mart_tech_demand` / `mart_platform_dist` / (선택) 정규화 효과 쿼리
- 차트 3개: 기술별 공고 수(표기변형 합쳐진 후) · 플랫폼별 분포 · 파티션별 누적 추이
- 로컬 fallback: BQ 접근 불가 시 `data/processed/postings_clean.parquet` 읽어 동일 차트
- 실행: `streamlit run app/dashboard.py` → 사용자가 스크린샷 + `mart_tech_demand` 결과 1건 캡처
- `requirements-dashboard.txt` (streamlit, google-cloud-bigquery, pandas, pyarrow)

### 5.7 `dags/collect_postings_dag.py`
`normalize` 뒤에 `upload_gcs` → `load_bq` → `dbt_build`(BashOperator: `dbt run && dbt test`) 태스크 추가.
DAG param `push_to_cloud: bool = False` — True일 때만 실행 (로컬 실행 보존).
`on_failure_callback` — 실패 시 `docs/airflow-run-logs/alerts/<dag_run_id>.json` 기록.

### 5.8 fallback / alert 실증
- **fallback**: collector가 개별 소스 실패를 manifest `failures=N`에 기록하고 계속 (구현됨). 문서화만
- **alert**: 빈 `dt=` 파티션으로 `load_to_bq.py` 1회 → `staging_rows==0` → raise → `on_failure_callback` 발화 → 알림 JSON 캡처

---

## 6. 산출 문서

`docs/6th-assignment/`:

| 파일 | 내용 | 언어 | 용도 |
|---|---|---|---|
| `decisions.md` | 이번 라운드 모든 결정: 무엇을 / 어떻게 정했나 / 대안 / 왜. 쉬운 말 | 한국어 | **발표 + 사용자 파악용** (사용자 명시 요청) |
| `consolidation.md` | 필수 7항목 매핑. 5차시 결과 인용 + 이번 클라우드 결과 | 한국어 | 제출 본문 |
| `stage-counts.md` | end-to-end 1회 단계별 건수 + 각 줄에 확인 명령(`bq query`, 로그 경로) | 한국어 | 필수항목 5 |
| `realism-design.md` | 4층 스택 상세, job tag 매핑 근거, 2층 로드맵 | 한국어 | 발표 + 다음 세션 |

추가:
- 구성도 갱신: `docs/diagrams/architecture-diagram-v1.html` + README mermaid (합성 일본어 트랙 꼬리 GCS→BQ→dbt→Streamlit 실선화, Looker는 점선 후보, ATS 트랙 별도 표기)
- `README.md` + `README.ja.md`: "6차시 — 클라우드 추가 트랙 + dbt + BI" 섹션 (로컬 실행법 유지 + 클라우드 실행법 추가)
- vault 동기화: 핵심 결정은 `03-projects/job-data-foundry/`에도 (부트캠프 발표 워크플로우 7번), MOC.md 링크

### 남은 작업 (consolidation.md §6)
dbt Conformed Dimension 마트 · Canonical Schema 전체 매핑(급여 파서·Taxonomy·tier) · 리얼리티 2층 LLM 문장뱅크 · 데이터 10만+ 스케일업 · 크론 스케줄 등록 · 동시성 경합 실험 · Kafka 트랙 장애 재현

---

## 7. 실행 순서 (체크포인트마다 제출 가능 상태 유지)

- [ ] **0. 외부 설계 repo 확인** — 완료 (§2)
- [ ] **1. 문서 뼈대** (오늘 밤) — `decisions.md`, `consolidation.md`(5차시까지 + §2 ADR), `realism-design.md` 초안. *이 시점에 최소 제출 가능*
- [ ] **2. job tag 데이터** (내일) — 다운로드 페이지 파일 포맷 확인 → `synth_rules.py` 풀 교체 → `verify_coverage.py` 통과
- [ ] **3. 템플릿 풀 + 볼륨** — `synth_templates.py` 작성, `N_ROLES` 상향, 생성기 재실행 → `data/raw/<platform>` → Kafka+Spark → `data/processed`
- [ ] **4. gcloud** — `brew install --cask google-cloud-sdk`; 사용자가 `!`로 `gcloud init`/`auth login`/`auth application-default login`; 프로젝트 ID 확정(`de-bootcamp`)
- [ ] **5. `cloud/setup.sh`** — API 활성화, 버킷·데이터셋
- [ ] **6. `cloud/` 3스크립트 구현 + GCS→BQ→MERGE 1회** — 단계별 건수 → `stage-counts.md`
- [ ] **7. `dbt/` 구현 + `dbt run && dbt test` 1회** — 마트 3개 + 테스트 통과 로그
- [ ] **8. DAG 클라우드 태스크 추가 + `airflow dags test ... -c '{"push_to_cloud": true}'` 1회** — 실행 로그
- [ ] **9. alert 실증** — 빈 파티션 1회 실패 → 알림 JSON 캡처
- [ ] **10. `app/dashboard.py` (Streamlit)** — 내가 작성 (BQ 마트 3쿼리 + 차트 3개 + 로컬 fallback) → 사용자가 `streamlit run` + 스크린샷 + `mart_tech_demand` 결과 1건
- [ ] **11. 문서 마무리** — `consolidation.md` 7항목 전부, `stage-counts.md`, 구성도, README(양 언어), vault 동기화
- [ ] **12. commit + push, 디스코드 링크 공유**

---

## 8. 리스크

- job tag 파일 포맷·구조 미확인 (내일 다운로드 페이지에서 확인). xlsx면 `openpyxl` 필요
- Spark/스크립트 → GCS 인증: `gcloud auth application-default login` 필수. 6단계에서 막히면 보고
- BQ parquet 로드 스키마 추론: `salary_min` 등 타입 이슈 가능 → 명시 스키마
- dbt BigQuery 어댑터(`dbt-bigquery`) + `profiles.yml` ADC 설정 첫 시도 — 7단계 시간 예측 어려움
- Streamlit BQ 인증(ADC) 첫 시도. 막히면 로컬 fallback(`data/processed` parquet)으로 동일 차트 → 스크린샷
- 마감까지 ~42시간. 1단계는 오늘 밤 완료해 최소 제출선 확보
