# 단계별 처리 건수 + 확인 방법

작성 2026-09-02 · 로컬 실행 기준 (클라우드 적재는 미착수 — [`consolidation.md`](consolidation.md) §6)

두 트랙이 별개다. 합산하지 않는다.

---

## 트랙 A — 합성 일본어 (표준화 파이프라인 검증)

2026-08-23 생성 스냅샷 기준.

| # | 단계 | 도구 | 건수 | 확인 방법 |
|---|---|---|---|---|
| 1 | 합성 생성 | `ingestion/generate_synthetic_postings.py` (N_ROLES=160) | **590** (7채널: hrmos 97·talentio 92·geekly 87·doda 82·company_site 79·openwork 79·mid_tenshoku 74 계열) | `python -c "import pandas,glob; print(sum(len(pandas.read_parquet(f)) for f in glob.glob('data/raw/*/*.parquet')))"` |
| 2 | Kafka 전송 | `streaming/producer.py` | **590** | producer stdout `sent=590` |
| 3 | Kafka 수신 | `streaming/consumer.py` | **590** | `wc -l data/kafka_landed/postings.jsonl` |
| 4 | Spark 전처리 | `streaming/spark_preprocess.py` | 전 **590** → 후 **575** | stdout `before=590 after=575`. 차이 15 = negative_control 제외 |
| 5 | 최종 저장 | Parquet | **575** (`posting_id` 중복 0) | `python -c "import pandas as p; d=p.read_parquet('data/processed/postings_clean.parquet'); print(len(d), d.posting_id.duplicated().sum())"` |
| 6 | 리포트 | `app/dashboard.py` (일본어 트랙) | KPI 공고 수 = **575** | 화면 상단 KPI. 자체검증 `python app/test_dashboard.py` |

**오류·미처리**: negative_control 15건은 설계상 제외(오류 아님). NFKC로 바뀐 직무명 0건
(이 스냅샷 직무명은 이미 정규 형태). 중복 제거 0건.

---

## 트랙 B — 실제 공개 ATS (시장 스냅샷) — 5차시 부하 실행 인용

| 실행 | 입력 | 수집(collect) | 정규화(Spark) 전→후 | 최종 저장 | 오류 |
|---|---|---|---|---|---|
| 베이스라인 (`dt=2026-08-30-baseline`) | companies=5, limit=20 | 20 | 20 → 20 | 20 (greenhouse 20) | failures=5 |
| 부하 증가 (`dt=2026-08-30-scaleup`) | companies=300 | 25,684 | 25,684 → 25,684 | 25,684 (greenhouse 22,110 / ashby 3,574) | failures=5 |
| 참고 (`dt=2026-08-26`) | companies=8 | 1,600 | 1,600 → 1,600 | 1,600 | — |

**확인 방법**:
- 수집: 실행 파티션의 `manifest.json` → `records`, `failures`, `companies_with_it_postings`
- 정규화: `spark_normalize_public_postings.py` stdout `before=N after=M saved_to=...`
- 최종 저장: `python -c "import pandas as p; a=p.read_parquet('data/golden-set/public-it-postings-canonical/dt=2026-08-30-scaleup'); print(len(a), a.source_platform.value_counts().to_dict(), a.posting_id.duplicated().sum())"`
- Airflow: `docs/airflow-run-logs/` 실행 로그 2건 (다른 파라미터), `airflow dags test collect_public_postings <date>`

**오류·미처리**: `failures=5`는 대상 회사에 공개 채용 보드가 없거나 404. manifest에 기록 후
계속 진행(fallback). `posting_id` 중복 0 — 한 실행 내 dedup + 파티션 덮어쓰기가 재실행 간 멱등 보장.

---

## 아직 없는 단계

GCS 업로드 파일 수 · BigQuery staging 로드 건수 · `MERGE` 후 canonical 총계 · dbt 마트 행 수
— 모두 클라우드 적재 미착수라 측정 불가. 다음 라운드.
