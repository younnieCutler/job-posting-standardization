# job-posting-standardization

일본 IT 채용 시장의 구인공고(JD, Job Description)를 여러 소스에서 모으면 표기 불일치가 발생합니다. 이를 표준화하는 데이터 파이프라인 프로젝트입니다. 데이터 엔지니어 부트캠프 라이브 스터디 과제 — 1차시(주제·데이터셋 선정)부터 4차시(Kafka+Spark 배치 전처리)까지 진행 중입니다.

**목표 한 줄**: 여러 채용 사이트/에이전트가 서로 다르게 표기한 같은 구인공고를 정규화·엔티티 해소해 신뢰할 수 있는 시장 분석 데이터로 만든다.

## 1. 프로젝트 주제

여러 채용 사이트/에이전트가 같은 회사의 같은 포지션을 각각 다른 필드명, 다른 값 형식으로 게재합니다. 이 현상을 일본 채용 도메인에서는 **表記ゆれ(표기 흔들림)** 라고 부릅니다.

| 항목 | 사이트 A | 사이트 B | 사이트 C |
|---|---|---|---|
| 직무명 필드 | `求人タイトル`(구인 제목) | `title` | `position_name` |
| 급여 | `年収400万〜600万円`(연봉, 약 ¥4M~6M) | `4000000`(숫자) | 상세 본문에 파묻힘 |
| 기술스택 | Python, AWS | python, aws | 본문 서술형 |

사람이 보면 같은 공고지만 시스템 입장에서는 필드명·값 형식·표기 방식이 전부 달라 별개의 데이터로 취급됩니다. 이 상태로 "Python 엔지니어 수요가 몇 건인가"를 집계하면 Python/python이 각각 따로 잡혀 시장 분석 수치가 왜곡됩니다.

이 프로젝트는 여러 소스에서 들어온 구인공고를 정규화하고 같은 자리를 식별(엔티티 해소)하는 파이프라인을 구축합니다.

**왜 이 프로젝트인가**: 이직 활동 중 여러 채용 에이전트를 동시에 이용하다 직접 겪은 문제입니다. 같은 공고인데도 사이트/에이전트마다 표기가 달라 비교·추적이 어려웠습니다. 사람이 손으로 대조하기엔 이미 늦은 규모라 시스템이 대신 정리하게 만들자는 데서 이 프로젝트가 출발했습니다.

### 가설 검증 — 인터뷰로 확인한 것과 반증된 것

처음엔 "기업 측에서 지원자 중복 접수로 수수료를 이중 청구받는 문제"까지 다루려 했습니다. 실제 일본 대기업 채용담당자를 인터뷰해 검증한 결과, 이 가설은 반증됐습니다. 정식 응모 시점에 매체별로 후보자 오너십이 자동 확정되고 응모 전에는 채용담당자가 후보자 개인정보를 열람조차 할 수 없는 구조라 중복 매칭이 개입할 여지 자체가 없었습니다.

반면 구인공고 표기 흔들림 문제는 인터뷰로 오히려 확인·보강됐습니다. 기업 내부는 Taxonomy로 표기를 통합 관리하고 있었지만 에이전트·잡보드·공홈·리퍼럴 4개 채널에 공고가 나갈 때는 채널별 담당자가 각각 따로 작성해 표기가 갈라졌습니다. 그래서 이 프로젝트는 지원자 중복 접수 문제는 접고 검증된 문제인 구인공고 표기 표준화에 범위를 좁혔습니다.

## 2. 데이터셋 선정 및 이유

### 왜 실제 스크래핑을 쓰지 않았는가

구인공고 실스크래핑은 각 사이트의 이용약관(ToS)·저작권 리스크가 있고 지속적으로 안정된 학습·검증용 데이터셋을 확보하기 어렵습니다. 대신 **Faker(`ja_JP`) 기반 합성 데이터 생성 + 소규모 실제 공고 표본(golden set) 검증** 방식을 채택했습니다.

### 2단 구조: golden set(패턴) + 합성 데이터(볼륨)

- **Golden set** (`docs/golden-set/real-postings-golden-set.csv`, 56행/19케이스): 실제 공개된 채용 공고를 6개 직무 그룹 전체에 걸쳐 수기로 채록한 표본입니다. "같은 공고가 사이트마다 어떻게 다르게 표기되는가"의 실제 패턴(필드명 변형, 급여 표기 방식, 시니어리티 등급 혼합 등)을 여기서 추출합니다.
- **문제점**: golden set은 회사 21곳(익명화)의 변주일 뿐이라 이 규칙을 그대로 복제하면 생성된 데이터가 그 21개 회사의 재탕처럼 보여 다양성이 죽습니다.
- **해결**: 역할 축(직무·회사·티어·근무지)과 패턴 축(golden set에서 채록한 표기 흔들림·급여 체계·티어 혼합)을 분리했습니다. 패턴 축은 golden set에서 가져오되 그 패턴이 적용되는 대상(직무명·회사·경력 등급)은 golden set 밖에서 폭넓게 뽑아 조합합니다. 이렇게 하면 표기 불일치라는 "일본 채용시장 특유의 지저분함"은 실증됐지만 매번 다른 조합으로 생성되어 볼륨 있는 데이터셋 역할을 할 수 있습니다.
- 생성기(`ingestion/generate_synthetic_postings.py`, `ingestion/synth_rules.py`)로 실 플랫폼 7종(hrmos/doda/geekly/openwork/mid_tenshoku/talentio/company_site) 스키마의 원시 데이터를 `data/raw/<platform>/*.parquet`(GCS Raw Zone 로컬 에뮬레이션)로 만들고, 정답지 `data/synthetic/ground_truth.csv`를 별도로 남깁니다. `ingestion/verify_coverage.py`로 회사/직군/플랫폼/티어/표기 패턴이 한쪽에 쏠리지 않았는지 자동 검증합니다.

상세 근거는 [`docs/architecture_decision_record.md`](docs/architecture_decision_record.md)의 ADR-005(Faker 합성 데이터 vs 실제 스크래핑)를 참고하세요.

## 3. 파이프라인 개요

```mermaid
flowchart TD
    A["합성 구인공고 7플랫폼<br/>GCS Raw Zone (Parquet)"] --> B["Spark<br/>Canonical Schema 매핑"]
    B --> C["BigQuery<br/>MERGE (posting_id 기준)"]
    C --> D["dbt Core<br/>변환 / 모델링"]
    D --> E["Looker Studio"]
```

- **처리 엔진**: Spark (ADR-001)
- **변환 레이어**: dbt Core (ADR-002)
- **오케스트레이션**: Airflow + BashOperator (ADR-004)
- **데이터 웨어하우스**: BigQuery (ADR-003)

기술 선택의 상세 트레이드오프는 [`docs/architecture_decision_record.md`](docs/architecture_decision_record.md)에 정리되어 있습니다.

전체 흐름을 시각화한 아키텍처 다이어그램은 [`docs/diagrams/architecture-diagram-v1.html`](docs/diagrams/architecture-diagram-v1.html)에서 확인할 수 있습니다.

## 4. 현재 상태 / 다음 단계

- 합성 데이터 생성기, golden set 검증, GCS Raw Zone(로컬 에뮬레이션) Parquet 저장까지 완료했습니다 (`data/raw/<platform>/`, tier 5단+null/unknown 예외, 실 플랫폼 7종).
- posting_id는 `sha256(source_platform + source_posting_id)` 결정적 해시로 생성해 BigQuery MERGE 키로 그대로 씁니다.
- Spark 정규화(Canonical Schema 매핑), dbt 모델링, Airflow DAG, BigQuery 적재는 이후 세션에서 구축 예정입니다.

### 4차시 과제 — Kafka + Spark 배치 전처리 (제출용, 메인 아키텍처와 별개)

라이브 스터디 4차시 공통 과제 대응용으로 `data/raw/<platform>/*.parquet` 뒤에 Kafka 구간을 얇게 추가했습니다. **JDF 메인 아키텍처(GCS→Spark Canonical 매핑→BigQuery MERGE→dbt→Airflow)는 이번 작업으로 바뀌지 않습니다** — JDF는 합성 배치 데이터라 원래 실시간 스트리밍이 필요 없는 도메인이고, 이 구간은 과제 제출 요건 충족용입니다.

**실행 명령**
```bash
pip install -r requirements.txt
docker compose up -d                    # Kafka(KRaft, 단일 노드) 기동
python streaming/producer.py            # data/raw/*/*.parquet -> Kafka topic jdf.raw_postings
python streaming/consumer.py            # topic -> data/kafka_landed/postings.jsonl
python streaming/spark_preprocess.py    # jsonl -> Spark 배치 전처리 -> data/processed/postings_clean.parquet
```

**메시지 명세** (topic: `jdf.raw_postings`, 값: `make_variant()` dict의 JSON 직렬화)

| 필드 | 타입 | 의미 |
|---|---|---|
| posting_id | string | sha256(source_platform+source_posting_id), BigQuery MERGE 키 |
| source_posting_id | string | 플랫폼 내 원본 공고 ID |
| source_platform | string | hrmos/doda/geekly/openwork/mid_tenshoku/talentio/company_site |
| role_id | string | 합성 역할(직무) ID |
| company_name | string | 회사명(Faker 생성) |
| raw_title | string | 원본 직무명(일본어) |
| job_family_group | string | 6개 직무 그룹 |
| tier | string | 시니어리티(junior~principal, null/unknown 예외 포함) |
| location_raw / location | string | 근무지 원문 표기 / 정규화 값 |
| salary_min / salary_max | int/null | 급여 범위(만엔) |
| salary_type / salary_text | string | 급여 표기 방식 / 원문 텍스트 |
| employment_type | string | 고용 형태 |
| agency | string/null | 에이전트 경유 여부 |
| posted_at | string/null | 게시일 |
| description_raw / requirements_raw / preferred_raw | string | 원문 설명/필수요건/우대요건 |
| is_negative_control | bool | 매칭 검증용 네거티브 샘플 여부 |
| tier_blended / coverage_gap_applied | bool | 티어 혼합 / 표기 누락 패턴 적용 여부 |

**Kafka 메시지 예시** (`data/kafka_landed/postings.jsonl` 1건)
```json
{
  "posting_id": "6a48f7dd400bf0b401f760b370fe109534c7bdcd9695191b96b73f1f96de8fb0",
  "source_posting_id": "company_site-113-0",
  "source_platform": "company_site",
  "role_id": "113",
  "company_name": "合同会社木村電気",
  "raw_title": "業務系SE",
  "job_family_group": "software_development",
  "tier": "mid",
  "location_raw": "勤務地：大阪府",
  "location": "大阪府",
  "salary_min": 485.0,
  "salary_max": 617.0,
  "salary_type": "月給制",
  "salary_text": "",
  "employment_type": "正社員",
  "agency": null,
  "posted_at": null,
  "description_raw": "職務内容：業務系SEとしてご活躍いただきます。",
  "requirements_raw": "必須要件：SQL・データ抽出経験3年以上",
  "preferred_raw": "求める経験・スキル：SQL実務経験、AWSまたはGCP実務経験、Python実務経験",
  "is_negative_control": false,
  "tier_blended": false,
  "coverage_gap_applied": false
}
```

**결과** (2026-08-23 로컬 실행 기준): Producer 전송 590건 = Consumer 수신 590건. Spark 전처리 전 590건 → 후 575건(negative_control 15건 제외, posting_id 중복 0건, raw_title NFKC 정규화 컬럼 추가).

**저장 위치/포맷**
- `data/kafka_landed/postings.jsonl` — Consumer가 적재한 raw JSON Lines
- `data/processed/postings_clean.parquet` — Spark 전처리 결과 (원본 컬럼 + `raw_title_normalized`, negative_control 제외, posting_id 중복 제거)

**실제 구현 vs 계획**: Kafka Producer/Consumer, Spark 배치 전처리(정규화·중복제거·필터)는 실제 구현·실행 완료. Canonical Schema 전체 매핑, BigQuery MERGE, dbt 모델링, Airflow 스케줄링은 이후 세션 계획대로 미구현 상태입니다.

## 저장소 구조

```
requirements.txt              # Faker, pandas, pyarrow, kafka-python, pyspark
docker-compose.yml             # Kafka(KRaft, 단일 노드) — 4차시 과제용
ingestion/
  generate_synthetic_postings.py
  synth_rules.py
  verify_coverage.py
streaming/                     # 4차시 과제용 (JDF 메인 아키텍처와 별개)
  producer.py
  consumer.py
  spark_preprocess.py
data/raw/                     # GCS Raw Zone 로컬 에뮬레이션 (플랫폼별 디렉토리, Parquet)
  hrmos/ doda/ geekly/ openwork/ mid_tenshoku/ talentio/ company_site/
data/kafka_landed/
  postings.jsonl              # Kafka Consumer 적재 결과
data/processed/
  postings_clean.parquet      # Spark 배치 전처리 결과
data/synthetic/
  ground_truth.csv            # 매칭 정답지 (role_id/posting_id/tier/company 등)
docs/
  architecture_decision_record.md
  golden-set/real-postings-golden-set.csv
  diagrams/architecture-diagram-v1.html
```
