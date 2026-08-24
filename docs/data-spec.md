# JDF Data Specification

**한국어 | [日本語](data-spec.ja.md)**

JDF 파이프라인이 다루는 데이터의 스키마·ID 정책·저장 위치 명세다. 설계 근거는 [`architecture_decision_record.md`](architecture_decision_record.md), 실행 방법은 [`../README.md`](../README.md)를 본다.

## 1. 데이터 레이어

| 레이어 | 위치 | 내용 |
|---|---|---|
| Raw | `data/raw/<platform>/*.parquet` | 플랫폼 7종 원본 스키마 그대로 (GCS Raw Zone 로컬 에뮬레이션) |
| Landed | `data/kafka_landed/postings.jsonl` | Kafka Consumer가 적재한 raw JSON Lines |
| Processed | `data/processed/postings_clean.parquet` | Spark 배치 전처리 결과 (원본 컬럼 + `raw_title_normalized`, negative_control 제외, posting_id 중복 제거) |
| Ground truth | `data/synthetic/ground_truth.csv` | 매칭 정답지 (role_id/posting_id/tier/company 등) |

Canonical Schema 매핑과 BigQuery Analytics 레이어는 미구현이다.

## 2. 플랫폼 (source_platform)

`hrmos` / `doda` / `geekly` / `openwork` / `mid_tenshoku` / `talentio` / `company_site`

## 3. ID 정책

`posting_id = sha256(source_platform + source_posting_id)`

결정적 해시라 재실행해도 같은 값이 나온다. BigQuery MERGE 키로 그대로 쓴다.

## 4. 일본어 처리

- `raw_title` 등 원문 필드는 그대로 보존한다.
- 정규화 값은 별도 컬럼으로 추가한다 (`raw_title_normalized` = NFKC 정규화).
- Taxonomy Mapping(직무명 → job_family_group)은 생성 단계에서 부여하며, 실 데이터 기준 매핑 규칙은 미구현이다.

## 5. 레코드 스키마

Kafka topic `jdf.raw_postings` 메시지와 Raw Parquet 레코드가 같은 필드 집합을 쓴다 (값은 `make_variant()` dict의 JSON 직렬화).

### 필드

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

### Kafka 메시지 예시 (`data/kafka_landed/postings.jsonl` 1건)
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

## 6. 품질 검증

- `ingestion/verify_coverage.py` — 회사/직군/플랫폼/티어/표기 패턴이 한쪽에 쏠리지 않았는지 자동 검증.
- `is_negative_control` — 매칭 검증용 네거티브 샘플. Spark 전처리에서 제외된다.
- tier 예외 — junior~principal 5단 외에 null/unknown을 의도적으로 섞어 결측 처리 경로를 검증한다.
- Golden set — [`golden-set/real-postings-golden-set.csv`](golden-set/real-postings-golden-set.csv) (56행/19케이스). 실제 공고의 표기 흔들림 패턴 원천.
