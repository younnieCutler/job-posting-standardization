---
title: "Architecture Decision Record — Japan IT Job Market & Candidate Integration Foundry"
date: 2026-07-09
tags: [project/de-bootcamp, career/data-engineering]
description: "JDF 프로젝트의 핵심 기술 선택(Spark vs DuckDB, dbt Core vs dbt Cloud, Snowflake vs BigQuery, Airflow+Cosmos vs dbt Cloud)의 배경과 트레이드오프를 면접 방어용으로 기록한 아키텍처 결정 로그."
---

# Architecture Decision Record — Japan IT Job Market & Candidate Integration Foundry

> 이 문서는 JDF(Job Data Foundry) 프로젝트에서 내린 주요 기술적 결정들을 **면접 방어 목적**으로 기록한 ADR(Architecture Decision Record)이다.  
> 각 항목은 "무엇을 선택했는가 → 왜 그 결정이 필요했는가 → 선택하지 않은 대안과의 트레이드오프"의 3단 구조로 기술한다.

---

## ADR-001: Spark vs DuckDB — 처리 엔진 선택

### 1. 결정 (Decision)

**Apache Spark를 PII 처리 구간의 변환 엔진으로 채택**하였다.  
DuckDB는 분석 쿼리 레이어(EDA, 경량 집계)에만 보조적으로 사용한다.

### 2. 맥락 (Context)

JDF 파이프라인에는 이력서, 후보자 식별 정보(성명, 생년월일, 연락처 등) 등의 **PII(Personally Identifiable Information)** 가 포함된 데이터가 흐른다. 이 PII 처리 구간을 DWH(Data Warehouse) 내부로 끌어들이면 다음과 같은 문제가 발생한다:

- DWH 내 PII 잔류 → 접근 제어 복잡성 증가
- PII가 분석 쿼리와 동일한 실행 컨텍스트를 공유 → 감사(Audit) 경계 불명확
- 파이프라인 경계가 모호해져 데이터 거버넌스 설계가 불투명하게 보임 (면접 관점에서도 불리)

Spark를 DWH **이전(upstream)** 구간에 배치함으로써 **PII 처리 → 비식별화/마스킹 → 정제된 데이터만 DWH 적재**라는 명확한 보안 경계(Security Boundary)를 파이프라인 설계 수준에서 강제할 수 있다.

### 3. 트레이드오프 (Trade-offs)

| 항목 | **Spark (선택)** | DuckDB (미선택) |
|---|---|---|
| **PII 격리** | DWH 외부에서 처리, 경계 명확 | 단일 프로세스 내 처리, 경계 불명확 |
| **운영 복잡도** | Docker Compose로 클러스터 구성 필요 | 단일 바이너리, 운영 단순 |
| **스케일** | 분산 처리 가능 (합성 데이터 규모에서는 과사양) | 단일 머신 최적화, 수십 GB까지 충분 |
| **면접 서사** | "보안 경계 설계를 의도했다"는 이야기 가능 | 단순 비용 절감 결정으로만 읽힐 수 있음 |
| **비용** | 로컬 Docker 기준 추가 컴퓨팅 자원 소모 | 거의 무비용 |

> **핵심**: 이 결정은 비용이나 스케일의 문제가 아니라, **파이프라인 설계에서 보안 경계를 어떻게 그을 것인가**의 문제다. Spark를 선택한 이유는 "PII를 DWH 밖에서 처리한다는 아키텍처 의도를 명시적으로 구현할 수 있기 때문"이다.

---

## ADR-002: dbt Core vs dbt Cloud — 변환 레이어 선택

### 1. 결정 (Decision)

**dbt Core(오픈소스)를 채택**하여 로컬 Docker Compose 환경 내에서 Airflow와 직접 연동한다.

### 2. 맥락 (Context)

JDF 프로젝트의 핵심 목표 중 하나는 **완전 로컬 재현 가능한(Fully Locally Reproducible) 파이프라인 데모**를 구성하는 것이다. 이는 다음 이유에서 중요하다:

- 면접관이 직접 `docker compose up` 한 번으로 전체 파이프라인을 실행할 수 있어야 함
- SaaS 계정 의존 없이 코드 자체가 포트폴리오의 증거가 되어야 함
- Public/Private 두 도메인이 하나의 마트 레이어로 수렴하는데, 마트 정의가 자주 바뀌는 상황에서 SQL만으로 빠르게 반복 + `dbt test`로 품질 자동검증

dbt Cloud는 Managed Scheduler와 IDE를 제공하지만, 이 경우 오케스트레이션 로직이 dbt Cloud의 SaaS 레이어 안에 숨겨져 로컬 재현이 불가능해진다.

### 3. 트레이드오프 (Trade-offs)

| 항목 | **dbt Core (선택)** | dbt Cloud (미선택) |
|---|---|---|
| **로컬 재현성** | `docker compose up`으로 완전 재현 가능 | SaaS 계정, API 키 필요 → 재현 불가 |
| **Airflow 연동** | `BashOperator`로 `dbt run` 직접 호출(v7, 아래 ADR-004 참고) | 자체 Scheduler 내장 → Airflow와 역할 중복 |
| **운영 편의** | 프로파일, 환경변수 직접 관리 필요 | UI 기반 관리, 초보자 친화적 |
| **비용** | 완전 무료 | 팀 플랜 이상에서 유료 |
| **면접 서사** | "오케스트레이션 전체를 직접 설계했다" 강조 가능 | SaaS가 대신 해준 것으로 오해받을 수 있음 |
| **기업 환경 유사성** | 대규모 엔터프라이즈에서 dbt Core + Airflow 조합 일반적 | 중소규모 팀, 스타트업에서 주로 선택 |

> **핵심**: dbt Core를 선택한 이유는 단순한 비용 절감이 아니라, **SQL만으로 마트를 빠르게 반복하고 `dbt test`로 품질을 자동검증**할 수 있기 때문이다.
>
> **[2026-07-26 갱신]** 이전 판본은 이 결정의 근거를 "Cosmos 연동 시연"으로 적었으나, v7 트리밍(개정 사유 v6→v7, `docs/job-data-foundry-design-spec.md`)에서 Cosmos를 제외하고 `BashOperator`로 확정했다. dbt Core 채택 자체는 유효하지만 근거를 교체함 — 자세한 내용은 ADR-004 참고.

---

## ADR-003: Snowflake vs BigQuery — DWH 선택

> **[2026-08-18 확정]** 아래 §1은 원래 "미결정"으로 남겨뒀던 판본이다. Batch Ingestion 구조 확정 시점에 **BigQuery**로 결정했다 — Looker Studio 무료 네이티브 연동(§3 비교표 그대로), `posting_id`(`sha256(source_platform + source_posting_id)`) 단일 컬럼 MERGE로 idempotency를 구현하는 것도 BigQuery `MERGE` 문 기준으로 설계했다. §2~§3의 트레이드오프 비교는 그대로 유효하므로 남겨둔다.

### 1. 결정 (Decision)

**BigQuery**. 위 갱신 노트 참고.

### 2. 맥락 (Context)

JDF 파이프라인의 서빙 레이어(Serving Layer)로 사용할 DWH를 선택해야 한다. 두 옵션 모두 각각 다른 강점을 가지고 있으며, **일본 채용 시장 컨텍스트**에서의 포지셔닝도 고려해야 한다.

- **Snowflake 우대 키워드**: 2024-2026년 일본 IT 채용 공고에서 Snowflake 언급 빈도가 증가 추세. 특히 데이터 엔지니어링 포지션에서 "Snowflake 경험자 우대" 조건이 다수 포함됨.
- **BigQuery 장점**: Google Looker Studio와 무료 네이티브 연동이 가능하여, 포트폴리오 대시보드를 별도 BI 툴 비용 없이 시각화할 수 있음.

### 3. 트레이드오프 (Trade-offs)

| 항목 | Snowflake | BigQuery |
|---|---|---|
| **일본 채용 시장 키워드** | ⭐ 우대 조건으로 자주 등장 | 상대적으로 적음 (GCP 스택 기업 한정) |
| **비용 모델** | 컴퓨팅(가상 웨어하우스) + 스토리지 분리 과금 | 쿼리 기반 과금 (소량은 무료 티어 활용 가능) |
| **BI 연동** | Tableau, PowerBI 연동 강점 | Looker Studio 무료 네이티브 연동 ⭐ |
| **로컬 에뮬레이션** | 불가 (클라우드 전용) | BigQuery Emulator(OSS) 로컬 사용 가능 |
| **dbt 호환성** | 완전 호환, 공식 어댑터 성숙 | 완전 호환, 공식 어댑터 성숙 |
| **학습 커브** | Snowflake SQL 방언 있음 | 표준 BigQuery SQL (ANSI 기반) |

**결정 기준**:
- 파이프라인 완성 이후 **일본 채용 공고 Snowflake 언급 비율이 40% 이상**이면 → Snowflake 선택
- 데모 시각화(Looker Studio 무료 연동)가 더 중요하다고 판단되면 → BigQuery 선택

> **현재 상태**: 파이프라인 코어(Ingestion → Transformation → Serving) 완성 후 실제 JD 분석을 통해 결정. 두 선택지 모두 dbt 어댑터가 완전히 지원되므로 전환 비용은 낮음.

---

## ADR-004: Airflow + BashOperator vs Cosmos — 오케스트레이션 방식

> **[2026-07-26 갱신 — 결정 반전]** 이 ADR의 이전 판본은 Cosmos 채택으로 기록돼 있었으나, `docs/job-data-foundry-design-spec.md`의 v7 트리밍 인터뷰(개정 사유 v6→v7)에서 결정이 뒤집혔다. 아래는 반전된 최종 결정과, 무엇이 왜 바뀌었는지의 기록이다.

### 1. 결정 (Decision)

**`BashOperator`로 `dbt run`을 직접 호출**한다. Airflow + astronomer-cosmos 조합은 채택하지 않는다(v7에서 v2 백로그로 연기).

### 2. 맥락 (Context)

Airflow에서 dbt를 실행하는 방법은 크게 두 가지다:

1. **BashOperator**: `bash_command="dbt run --select ..."` 로 dbt를 subprocess로 실행. 구현이 단순하지만 dbt 내부 모델 단위의 성공/실패가 Airflow UI에 노출되지 않음.
2. **Cosmos(astronomer-cosmos)**: dbt 프로젝트를 파싱하여 **dbt 모델 하나하나를 Airflow Task로 변환**하고, 모델 간 의존성(lineage)을 Airflow TaskGroup으로 시각화함.

v7 트리밍 인터뷰(코드 0줄 상태에서 스코프부터 재점검)에서 이 프로젝트의 노스스타(데이터 표준화 + 데이터 거버넌스) 기준으로 재판정한 결과, Cosmos는 **"Airflow UI에서 dbt 리니지가 예쁘게 보인다"는 편의 기능이지 표준화나 거버넌스 어느 축도 아니다**는 결론에 도달했다. 의존성 하나를 줄이는 것이 완주 리스크를 낮춘다는 판단도 작용했다.

### 3. 트레이드오프 (Trade-offs)

| 항목 | **BashOperator (선택)** | Airflow + Cosmos (미선택) |
|---|---|---|
| **노스스타 적합성** | 표준화·거버넌스 어느 축에도 필요조건 아님 — Airflow 기본 기능만으로 정규화→적재→매칭 순서관리는 충분 | dbt 리니지 시각화는 편의 기능, 두 축 어디에도 안 걸림 |
| **설치 복잡도** | Airflow 기본 기능만으로 구현 가능 ⭐ | `pip install astronomer-cosmos` 추가 필요 |
| **완주 리스크** | 의존성 하나 적음 ⭐ | manifest.json 파싱 등 새로 배워야 할 표면적 증가 |
| **dbt 리니지 시각화** | dbt 내부 블랙박스, Airflow는 1개 Task만 보임 | Airflow UI에 모델 단위 Task로 표현 |
| **Task 단위 재시도** | 전체 dbt run 재실행 | 실패한 dbt 모델만 선택적 재시도 가능 |
| **v2 확장 여지** | Cosmos는 v2 백로그로 보류 — 필요해지면 언제든 추가 가능 | — |

> **핵심**: BashOperator를 선택한 이유는 "쉬운 길을 택해서"가 아니라, **이 프로젝트가 증명하려는 두 축(표준화/거버넌스) 중 어디에도 Cosmos가 필요조건이 아니라는 노스스타 판정** 때문이다. dbt 리니지가 Airflow UI에 예쁘게 보이는 건 좋은 기능이지만, 이 프로젝트가 증명해야 할 것은 아니다 — v2 확장 아이디어로 남겨둔다.

---

## ADR-005: Faker 합성 데이터 vs 실제 스크래핑 — 데이터 소스 전략

### 1. 결정 (Decision)

**Python `Faker` 라이브러리(ja_JP 로케일)를 사용한 합성 데이터**를 파이프라인의 주 데이터 소스로 채택한다.  
실제 채용 사이트(doda, Green, Wantedly 등) 스크래핑은 수행하지 않는다.

### 2. 맥락 (Context)

JDF 프로젝트는 일본 IT 채용 시장 데이터를 다루지만, 실제 사이트 스크래핑에는 다음과 같은 명확한 리스크가 존재한다:

- **ToS(이용 약관) 위반**: doda, Green, Wantedly 등 주요 채용 플랫폼은 자동화된 데이터 수집을 명시적으로 금지하고 있음
- **법적 리스크**: 일본 부정경쟁방지법, 개인정보보호법(個人情報保護法) 위반 가능성
- **포트폴리오 공개 리스크**: 스크래핑으로 수집한 실제 데이터를 GitHub에 공개하면 법적 문제가 될 수 있음

반면, Faker 합성 데이터는 **의도적 노이즈 주입**이 가능하다는 독자적 강점이 있다:

- 실제 일본 데이터에서 발생하는 **표기ゆれ 패턴**(전각/반각 혼용, 한자/가나/영문 혼재, 급여 표기 불일치 등)을 파이프라인에 의도적으로 주입
- 파이프라인의 **정규화/정제(Normalization) 역량**을 데모하는 것이 가능해짐
- 실제 스크래핑보다 오히려 **엔지니어링 역량 증명에 더 유리**한 데이터를 생성할 수 있음

### 3. 트레이드오프 (Trade-offs)

| 항목 | **Faker 합성 데이터 (선택)** | 실제 스크래핑 (미선택) |
|---|---|---|
| **법적 리스크** | 없음 ⭐ | ToS 위반, 법적 책임 가능성 |
| **포트폴리오 공개** | GitHub 공개 완전 무방 ⭐ | 실데이터 공개 → 법적/윤리적 문제 |
| **노이즈 주입 제어** | 의도적 패턴 설계 가능 ⭐ | 실제 노이즈 발생 패턴만 따름 |
| **데이터 실재성** | 합성이므로 실제 시장 반영 제한 | 실제 시장 동향 반영 |
| **반복 생성** | 시드 고정으로 재현 가능한 데이터셋 생성 | 스크래핑 타이밍에 따라 달라짐 |
| **엔지니어링 난이도 데모** | 정규화 로직 설계 역량 증명 ⭐ | 정제 역량보다 수집 역량 부각 |

> **핵심**: 합성 데이터를 선택한 이유는 "실데이터가 없어서"가 아니라, **ToS 위반 없이 포트폴리오를 공개하면서, 동시에 파이프라인의 정규화 역량을 의도적으로 설계·데모할 수 있기 때문**이다. 이는 면접관의 "실제 데이터가 없으면 의미 없지 않나?" 반문에 대한 선제 방어이기도 하다.

---

## Related Content to Explore

- [job-data-foundry-design-spec](file:///Users/macbook/dev/career/job-data-foundry/docs/job-data-foundry-design-spec.md)
- [pii_handling_policy](file:///Users/macbook/dev/career/job-data-foundry/docs/pii_handling_policy.md)
- [entity_resolution_rules](file:///Users/macbook/dev/career/job-data-foundry/docs/entity_resolution_rules.md)
