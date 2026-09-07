# JDF Looker Studio 종합 BI 리포트 설계

작성 2026-09-07 · 대상 사용자: 일본 IT/글로벌 기업의 HR·TA·채용 데이터 분석 담당자
관련: [`consolidation.md`](consolidation.md) · dbt 마트: `bright-link-507313-q3.jdf.*`

---

## 0. 데이터 가용성 (설계의 전제)

| 데이터셋 | 정체 | 현재 위치 | 리포트에서 쓰는 범위 |
|---|---|---|---|
| **Public ATS** | Greenhouse·Ashby 공개 API 실채용공고 25,684건 (greenhouse 22,110 / ashby 3,574) | **로컬 parquet만** (`data/golden-set/public-it-postings-canonical/dt=*/`) — BigQuery 미적재 | 시장 관측 분석 (공고 수·기업·직무명·지역·채널·본문 기술 키워드) |
| **Japan Synthetic** | 표기 흔들림·파이프라인 검증용 합성 일본어 공고 575건 | **BigQuery `jdf` 적재 완료** (`stg_postings` + 7개 마트) | 표준화 결과·데이터 품질만 |

**절대 규칙**: 두 데이터셋을 한 화면·한 KPI로 합치지 않는다. 페이지 헤더에 어느 데이터인지 항상 표기.

**현재 BigQuery `jdf`에 있는 것 (Synthetic)**

| 테이블 | 내용 |
|---|---|
| `stg_postings` | 공고 1건 = 1행. `job_family_group`, `tier`, `salary_type`, `location`, `posted_month`, `skills`(문자열 배열) |
| `mart_tech_demand` | 기술 키워드별 공고 수 (표기 변형 합산 후) |
| `mart_platform_dist` | 채널별 공고 수 + 기술 키워드 부착률 |
| `mart_seniority_dist` | 직무 분야 × 경력 수준별 공고 수 |
| `mart_salary_format` | 급여 **표기 방식** 분포 (금액 아님) |
| `mart_company_activity` | 공고 많은 기업 상위 20 |
| `mart_monthly_intake` | 월별 공고 유입 (`posted_at` 있는 48%만) |
| `mart_overview` | 요약 스코어카드 1행 |

**아직 없는 것 (임의로 만들지 않음)**
- Public ATS 데이터의 BigQuery 적재 → **Page 2·3의 시장 분석은 이 적재가 선행돼야 함**
- 급여 금액 파싱 (`salary_min/max`는 전부 NULL, `salary_type` 문자열만 존재)
- 직무 분류(taxonomy)를 ATS `title`에 적용하는 로직 (Synthetic만 `job_family_group` 보유)
- ATS `description` 기술 키워드 추출 마트 (로직은 `SKILL_KEYWORDS` regex로 재사용 가능, 마트 미생성)

---

## 1. 전체 페이지 구조

| # | 페이지 | 데이터셋 | 핵심 질문 | 상태 |
|---|---|---|---|---|
| 1 | Executive Summary | ATS / Synthetic **각각** 요약 (합산 없음) | "데이터에 무엇이 들어 있고 어떤 특징인가?" | ATS 부분은 적재 후 |
| 2 | Job Demand (직무별 채용 현황) | **Public ATS** | "어떤 직무·경력·기업·지역의 공고가 많이 관측되는가?" | ATS 적재 후 |
| 3 | Skill Signals (기술 수요 신호) | **Public ATS** (본문 키워드) | "공고에서 어떤 기술 키워드가 많이 나타나는가?" | ATS 적재 후 |
| 4 | Standardization & Data Quality | **Japan Synthetic** | "제각각 들어온 데이터를 얼마나 일관되게 정리했는가?" | **지금 구현 가능** |
| 5 | Methodology & Data Source | — | "이 수치를 어디까지 믿을 수 있는가?" | 지금 구현 가능 |

- Page 2·3의 "직무 분야 × 경력 수준" 축은 **ATS에 없다**(ATS엔 `tier`/`job_family` 없음). 이 축의 분석은 Synthetic에만 있고, Page 4에서 **"합성 데이터 구성 분포 — 실제 시장 수요 아님"** 캡션과 함께만 보여준다.

---

## 2~10. 페이지별 상세

### PAGE 1 — Executive Summary

**2. Persona 질문**: 지금 이 데이터에 무엇이 들어 있나? 실데이터인가 합성인가? 언제 기준인가?

**3. KPI (ATS 블록 / Synthetic 블록 분리, 각 4~5개)**

| ATS 블록 (헤더: "Public ATS 수집 데이터 기준") | Synthetic 블록 (헤더: "Japan Standardization Test Dataset — Synthetic") |
|---|---|
| 관측 공고 수 (25,684) | 검증 공고 수 (575) |
| 관측 기업 수 (distinct `company_name`) | 검증 기업 수 (165) |
| 수집 채널 수 (2 — greenhouse·ashby) | 관측 직무 분야 수 (6) |
| 수집 지역 수 (distinct `location`) | 채용 채널 수 (7) |
| 데이터 기준일 (`collected_at` 최대) | 데이터 기준일 (`posted_at` 최대, 커버리지 48% 주석) |

**4. 추천 차트**: 스코어카드 행 2줄(ATS/Synthetic) + 각 데이터셋 "채널별 공고 수" 가로 막대 1개씩(작게). 그 외 차트 없음 — 요약 페이지는 숫자만.

**5. Dimension**: `source_platform`, `collected_at`(ATS) / `posted_month`(Synthetic)
**6. Metric**: `공고 수`(Record Count 또는 `postings`), `CTD(기업)`, `CTD(근무 지역)`
**7. Filter**: 없음 (요약은 전체). 페이지 상단에 데이터셋 라벨만.
**8. 표시 컬럼명**: 아래 §5 규칙표.
**9. Calculated Field**: 없음 (스코어카드는 기본 집계).
**10. 잘못된 해석 주의**:
- ATS 25,684 + Synthetic 575를 더해 "26,259건 시장"이라고 말하지 않는다.
- ATS는 "수집 대상 기업 내 관측 결과"지 "일본 채용시장 규모"가 아니다.
- 채널 수 2는 "일본에 ATS가 2개"가 아니라 "우리가 수집한 API가 2종"이다.

---

### PAGE 2 — Job Demand (Public ATS)

**2. Persona 질문**: 어떤 직무·기업·지역의 공고가 많이 관측되는가?

**3. KPI (4개)**: 관측 공고 수 · 관측 기업 수 · 상위 20개 기업이 차지하는 공고 비중(%) · 공고당 평균 직무명 길이(선택)

**4. 추천 차트**

| 차트 | 질문형 제목 | 형태 |
|---|---|---|
| 기업별 공고 수 Top 20 | "어떤 기업에서 공고가 많이 관측됐나?" | 가로 막대, 내림차순 |
| 근무 지역별 공고 수 Top 15 | "공고는 어떤 지역에서 많이 관측됐나?" | 가로 막대 |
| 부서(`department`)별 공고 수 Top 15 | "어떤 부서 채용이 활발히 관측됐나?" | 가로 막대 |
| 채널별 공고 수 | "공고는 어떤 채널에서 많이 관측됐나?" | 가로 막대 (greenhouse/ashby) |
| (참고 탭) 정리된 직무명 상위 30 | "가장 자주 등장한 직무명은?" | 표 |

- **직무 분야 × 경력 수준 히트맵은 이 페이지에 넣지 않는다.** ATS엔 그 축이 없다. Page 4에 Synthetic 기준으로만.

**5. Dimension**: `company_name`, `location`, `department`, `source_platform`, `title_normalized`
**6. Metric**: `공고 수` (Record Count), `상위 N 비중`(계산 필드)
**7. Filter**: 기업 · 근무 지역 · 부서 · 채용 채널 (드롭다운). 경력 수준·직무 분야 필터는 **데이터에 없어 넣지 않음**.
**8. 표시 컬럼명**: `company_name`→기업, `location`→근무 지역, `department`→부서, `source_platform`→채용 채널, `title_normalized`→정리된 직무명.
**9. Calculated Field**:
- `상위20_기업_공고비중` = 상위 20 기업 공고 합 ÷ 전체 (리포트 레벨 계산 또는 BQ 뷰). 간단히는 별도 지표 표로 대체.
**10. 잘못된 해석 주의**:
- "공고 수 = 경쟁 강도/경쟁률"로 해석 금지. 공고 수만으로 지원자 대비 경쟁률을 알 수 없다. → "채용 수요 / 공고 분포 / 관측 공고 수"라고만.
- greenhouse에 공고 많은 = 그 회사가 채용을 많이 한다 아님. greenhouse를 쓰는 회사가 수집 표본에 많이 포함됐다는 뜻.
- 지역은 회사가 적은 원문이라 표기 흔들림 있음(원문 `location`). "정리 전 값" 주석.

---

### PAGE 3 — Skill Signals (Public ATS 본문)

**2. Persona 질문**: 공고 본문에서 어떤 기술 키워드가 많이 나타나는가?

**3. KPI (3개)**: 기술 키워드 하나라도 포함한 공고 비율 · 공고당 평균 키워드 수 · 관측된 distinct 키워드 수

**4. 추천 차트**

| 차트 | 질문형 제목 | 형태 |
|---|---|---|
| 기술 키워드 Top 15 | "공고에서 많이 관측된 기술 키워드는?" | 가로 막대 |
| 채널별 상위 키워드 | "채널마다 요구 기술이 다른가?" | 100% 누적 막대 또는 히트맵 |
| (선택) 상위 기업 × 상위 키워드 | "특정 기업이 특정 기술을 집중적으로 요구하나?" | 히트맵 |

**5. Dimension**: `skill`(본문에서 추출한 키워드), `source_platform`, `company_name`
**6. Metric**: `공고 수` (해당 키워드 포함 공고 distinct count)
**7. Filter**: 채용 채널 · 기업 · 키워드
**8. 표시 컬럼명**: `skill`→기술 키워드. 화면 문구는 "통합된 기술 키워드" / "공고에서 관측된 기술 키워드". 도움말: "같은 기술의 표기 변형(예: Python/パイソン/PYTHON)을 하나로 합산".
**9. Calculated Field / 선행 작업**:
- **BQ에 `mart_ats_skill_demand` 필요** (미구현). `stg_postings`의 `SKILL_KEYWORDS` regex 15종을 ATS `description_normalized`에 `REGEXP_CONTAINS`로 적용해 키워드별 공고 수 집계. Synthetic `mart_tech_demand`와 동일 구조.
**10. 잘못된 해석 주의**:
- regex 키워드 매칭이다. "Canonical Skill" / "Skill Taxonomy"라고 부르지 않는다. → "통합된 기술 키워드".
- `Go`, `React` 등 짧은 단어는 오탐 가능(단어 경계 regex로 완화했으나 100% 아님). 주석.
- 키워드 미검출 = 그 기술을 안 쓴다 아님. 본문에 명시 안 했을 수 있음.

---

### PAGE 4 — Standardization & Data Quality (Japan Synthetic) ★ JDF 차별점

**2. Persona 질문**: 여러 출처에서 다르게 들어온 데이터를 얼마나 일관되게 만들었는가?

**3. KPI (실제 계산 가능한 것만, 4~5개)**

| KPI | 계산 | 소스 |
|---|---|---|
| 입력 공고 수 | Kafka producer 전송 건수 (590) | `stage-counts` (파이프라인 로그) |
| 처리 후 공고 수 | `COUNT(*)` `stg_postings` (575) | BQ |
| 제거된 레코드 수 | 590 − 575 = 15 (negative_control) | 계산 필드 |
| posting_id 중복 수 | `COUNT(*) − COUNT(DISTINCT posting_id)` = 0 | BQ |
| 기술 키워드 부착률 | `mart_platform_dist` 가중평균 (≈0.977) | BQ |
| 급여 표기 방식 가짓수 | `mart_overview.salary_format_variants` (3) | BQ |
| `posted_at` 채워진 비율 | `mart_overview.posted_at_coverage` (0.48) | BQ |

**하드코딩·임의 지표 금지.** "정규화 후 = 1" 같은 것 넣지 않는다.

**4. 추천 차트**

| 차트 | 질문형 제목 | 형태 |
|---|---|---|
| 원본 직무명 → 정리된 직무명 사례 | "표기만 다르고 뜻은 같은 데이터를 어떻게 통일했나?" | 표 (before/after 2열, 5~10행 예시) |
| 급여 표기 방식 분포 | "급여는 몇 가지 방식으로 적혀 있나?" | 가로 막대 (원형 대신 — 비율 비교 목적이면 도넛 1개 허용) |
| 직무 분야 × 경력 수준 | "합성 데이터는 어떤 직무·경력 구성으로 만들어졌나?" | 누적 막대. **캡션 필수: "합성 데이터 구성 분포 — 실제 시장 수요 아님"** |
| 값이 비어있는 항목 비율 | "어떤 항목이 자주 비어 있나?" | 가로 막대 (근무 지역/급여표기/게시일 등 null 비율) |
| 월별 공고 유입 | "합성 공고는 어느 시점 분포로 생성됐나?" | 시계열. 캡션: "`posted_at` 있는 48%만" |

**5. Dimension**: `raw_title`·`raw_title_normalized`(예시 표), `salary_type`, `job_family_group`, `tier`, `posted_month`
**6. Metric**: `공고 수`(Record Count), null 비율(계산 필드)
**7. Filter**: 직무 분야 · 경력 수준 (Synthetic 내부 탐색용). 데이터셋 라벨 고정.
**8. 표시 컬럼명**: `raw_title`→원본 직무명, `raw_title_normalized`→정리된 직무명, `salary_type`→급여 표기 방식, `job_family_group`→직무 분야, `tier`→경력 수준. 화면에서 NFKC·Canonical·Taxonomy 대신 "문자 표기 통일" / "표준화된 값" / "직무 분류". 기술어는 도움말로.
**9. Calculated Field**:
- `제거된_레코드수` = 590 − `total_postings` (입력 590은 파이프라인 고정값 → 파라미터/상수 필드)
- `근무지역_공백비율` = `COUNTIF(location IS NULL) / COUNT()`
- `게시일_공백비율` = `1 − posted_at_coverage`
- `급여표기_공백비율` = `COUNTIF(salary_type IS NULL) / COUNT()`
- (before/after 표는 `postings_canonical`에서 `raw_title != raw_title_normalized` 필터 → 계산 필드 `표기변경여부`)
**10. 잘못된 해석 주의**:
- 이 페이지의 575건·직무 분포·급여 표기를 **실제 일본 시장 수요/급여로 읽지 않는다.** 합성 데이터의 목적은 "표기 흔들림을 얼마나 정리했나" 검증.
- 급여 표기 방식(月給制/年俸制/…) 분포는 "표기가 몇 갈래로 갈리는가"이지 급여 수준이 아니다. 금액 파싱은 미구현.
- `raw_title_normalized`가 원본과 같은 행이 많다 = 이미 정규형으로 생성된 합성 데이터라서. "이번 스냅샷에서 변경 N건" 실측치만.

---

### PAGE 5 — Methodology & Data Source

**2. Persona 질문**: 이 수치를 어디까지 믿을 수 있는가?

**4. 표시 요소** (차트 아님, 텍스트·표·다이어그램)

| 항목 | Public ATS | Japan Synthetic |
|---|---|---|
| 출처 | Greenhouse·Ashby 공개 ATS API | `generate_synthetic_postings.py` (Faker, SEED=42) |
| 수집 방법 | 공개 JSON 엔드포인트 순회. **HTML 스크래핑·로그인 영역·지원자 개인정보 미접근** | 결정적 생성 (규칙 기반, 런타임 LLM 없음) |
| 데이터 기준일 | `collected_at` (수집 시각) | `posted_at` (생성 시 부여, 48%만) |
| 실데이터 여부 | 실제 공개 공고 | 합성 |
| 포함 범위 | greenhouse·ashby를 쓰는 IT·글로벌 기업 표본. 미국·글로벌 중심 | 일본어 IT 공고 형태의 표기 변형 케이스 |
| 제외 범위 | 그 외 ATS·자사 채용페이지·에이전트 비공개 공고 | 실제 기업·실제 급여·실제 시장 규모 |
| 알려진 한계 | "일본 전체 시장"이 아님. 채널 편향. 지역·직무명 원문 표기 흔들림 | 시장 수요·급여 해석 불가. 볼륨 575로 축소 상태 |

**처리 흐름도** (mermaid 또는 이미지):

```
소스(공개 ATS API / 합성 생성기)
  → 원본 데이터 보관 (parquet)
  → 문자 표기 통일 (NFKC) · 중복 제거 (posting_id 해시)
  → 직무/스킬 정리 (직무 분류 · 기술 키워드 통합)  ※ 직무 분류는 Synthetic만
  → BigQuery 적재 (MERGE ON posting_id)            ※ 현재 Synthetic만
  → dbt 마트
  → Looker Studio
```

**7. Benchmark 표** (마지막, 간단히)

| 참고 서비스 | 참고한 점 | JDF 적용 |
|---|---|---|
| HRog | 일본 채용시장 분석 | 직무·경력·채널 분석 (Page 2) |
| Lightcast | 직무·스킬 표준화 | 표기 통일·직무 분류 (Page 4) |
| Revelio Labs | 의사결정형 HR 리포트 | 페이지를 "무슨 결정을 내리나" 중심 구성 |
| TheirStack | JD 구조화·스킬 추출 | 기술 키워드 분석 (Page 3) |

**10. 잘못된 해석 주의**: 이 리포트는 두 개의 별개 데이터를 담는다. 한 페이지의 결론을 다른 데이터셋에 전이하지 않는다.

---

## 5. 사용자용 컬럼명 규칙 (전 페이지 공통)

| 내부명 | 화면 표시 |
|---|---|
| `source_platform` | 채용 채널 |
| `company_name` | 기업 |
| `job_family_group` | 직무 분야 |
| `tier` | 경력 수준 |
| `raw_title` | 원본 직무명 |
| `raw_title_normalized` / `title_normalized` | 정리된 직무명 |
| `salary_min` | 최저 연봉 |
| `salary_max` | 최고 연봉 |
| `salary_type` | 급여 표기 방식 |
| `postings` / Record Count | 채용공고 수 |
| `location` / `location_raw` | 근무 지역 |
| `department` | 부서 |
| `description_raw` / `description_normalized` | 채용공고 내용 |
| `collected_at` | 수집 시각 |
| `posted_month` | 게시 월 |
| `skill` | 기술 키워드 |
| `posting_id`, `source_record_sha256` | **숨김** (일반 리포트 비노출) |

---

## 9. Looker Studio Calculated Field 모음

| 필드명 | 정의 | 페이지 |
|---|---|---|
| `상위20_기업_공고비중` | (상위 20 기업 공고 합) / (전체 공고) ×100 — 리포트 레벨 또는 BQ 뷰 | 2 |
| `키워드포함_공고비율` | `COUNTIF(array_length(skills)>0) / COUNT()` | 3, 4 |
| `공고당_평균키워드수` | `SUM(키워드매칭수) / COUNT()` | 3 |
| `제거된_레코드수` | `590 - total_postings` (590 = 파이프라인 입력 상수) | 4 |
| `근무지역_공백비율` | `COUNTIF(location IS NULL) / COUNT()` | 4 |
| `게시일_공백비율` | `1 - posted_at_coverage` | 4 |
| `급여표기_공백비율` | `COUNTIF(salary_type IS NULL) / COUNT()` | 4 |
| `표기변경여부` | `CASE WHEN raw_title != raw_title_normalized THEN "변경됨" ELSE "동일" END` | 4 |
| `데이터셋_라벨` | 상수 텍스트 필드 ("Public ATS 관측" / "Synthetic 검증") | 전 페이지 헤더 |

---

## 11. 실제 구현 순서

### A. 지금 구현 가능 (Synthetic만, BQ 적재 완료)
1. **Page 4 (Standardization & Data Quality)** — `stg_postings`, `mart_overview`, `mart_salary_format`, `mart_seniority_dist`, `mart_monthly_intake`, `postings_canonical`(before/after 표). 계산 필드 §9의 4·근무지역/게시일/급여표기 공백비율·표기변경여부.
2. **Page 5 (Methodology)** — 텍스트·표·흐름도. 데이터 없이 작성.
3. **Page 1 의 Synthetic 블록** — `mart_overview` 스코어카드 5개.

### B. Public ATS 적재 후 (선행 작업 필요)
4. `cloud/upload_to_gcs.py --src data/golden-set/public-it-postings-canonical/dt=<date> --prefix ats` → GCS
5. `cloud/load_to_bq.py` 변형 또는 신규 스크립트로 `jdf.ats_postings` 테이블 적재 (ATS 스키마 별도 — synthetic canonical과 섞지 않음)
6. dbt 신규 모델:
   - `stg_ats_postings` (ATS 타입 캐스팅 + `SKILL_KEYWORDS` regex를 `description_normalized`에 적용 → `skills` 배열)
   - `mart_ats_company` (기업별 공고 수 Top N)
   - `mart_ats_location` (지역별)
   - `mart_ats_department` (부서별)
   - `mart_ats_skill_demand` (키워드별 공고 수)
   - `mart_ats_overview` (스코어카드 1행)
7. `dbt run && dbt test`
8. **Page 2 (Job Demand)** — `mart_ats_company/location/department` + `stg_ats_postings`(채널·직무명)
9. **Page 3 (Skill Signals)** — `mart_ats_skill_demand` + `stg_ats_postings`(채널·기업 교차)
10. **Page 1 의 ATS 블록** — `mart_ats_overview` 스코어카드

### C. 마감
11. 전 페이지 헤더에 데이터셋 라벨 확인 → 5초 안에 "어느 데이터인가" 판별되는지 점검 → 캡처 → `docs/7th-assignment/captures/14-looker-*.png` 교체 → README §3 반영 → 커밋

### 마감 리스크 (7차시 오늘 17:00)
- B(ATS 적재 + 5개 마트 + dbt run)는 시간 소요. 못 하면 **A만으로 제출** — Page 4·5 + Page 1 Synthetic 블록. Page 2·3은 리포트에 "Public ATS 적재 후 추가 (다음 단계)" 안내 페이지로 대체.
- 클라우드 리소스 조작(ATS 적재·dbt run)은 사용자 명시 지시 후에만.
