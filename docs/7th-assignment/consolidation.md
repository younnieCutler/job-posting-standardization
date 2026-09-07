# 7차시 과제 제출 본문 — 서빙 레이어 + 최종 발표

작성 2026-09-06 · 마감 2026-09-07(월) 17:00
캡처: [`captures/`](captures/) · 원샷 실행: [`../../scripts/run_pipeline.sh`](../../scripts/run_pipeline.sh)

## 한 줄 요약

새 기능을 붙이는 대신 **이미 만든 것을 입력→처리→저장→읽기까지 한 번의 실행으로 잇고**,
문서를 코드 상태와 일치시키고, 클라우드 계층은 스크립트까지만 작성(실행은 수동 게이트)했다.

## 6파트 → 산출물 매핑

| # | 파트 | 산출물 | 캡처 |
|---|---|---|---|
| 1 | 문제와 데이터 | README §1·§2, `docs/golden-set/` (표기 흔들림 56행) + 합성 590 + ATS 25,684 | — |
| 2 | 파이프라인 구조 + 데이터 모델 | README §3 mermaid(실제 2트랙), `docs/diagrams/architecture-diagram-v1.html`, `posting_id` 해시 키 | 18 |
| 3 | 실행 결과 표 | `scripts/run_pipeline.sh` 단계별 건수 (아래 표) | 01, 02 |
| 4 | 부하·장애·복구 + 아직 보장 못하는 것 | 5차시 3종(`docs/loadtest-logs/evidence.md`) + MERGE 멱등 설계(`cloud/load_to_bq.py`) | 17 |
| 5 | 저장 결과를 쓰는 장면 | `scripts/read_result.py` 출력 / Streamlit / `cloud/query_marts.py`(SQL) | 03·04·05 |
| 6 | 남은 문제와 다음 단계 | 아래 "남은 문제" | — |

## 3. 실행 결과 — 원샷 실행 단계별 건수

`bash scripts/run_pipeline.sh` (2026-09-06 로컬 실행, 캡처 01):

| 단계 | 건수 |
|---|---|
| 1. 생성 (`data/raw/<platform>/*.parquet`, 7종) | 590 |
| 2. Kafka Producer 전송 (`topic jdf.raw_postings`) | 590 |
| 3. Kafka Consumer 수신 (`data/kafka_landed/postings.jsonl`) | 590 |
| 4. Spark 전처리 전 | 590 |
| 5. Spark 전처리 후 → `data/processed/postings_clean.parquet` | 575 |

- 전/후 차이 15 = `is_negative_control`(의도적으로 심은 "비슷하지만 다른 공고") 제외
- `posting_id` 중복 0
- 매 실행 `docker compose down && up -d`로 Kafka 토픽 초기화 → 재실행해도 590→590→590→575 동일 (멱등, 캡처 01을 2회분 비교)

## 5. 서빙 — 저장 결과를 읽는 장면

`python scripts/read_result.py` (캡처 03 대체 가능한 스크립트 출력):

```
공고 수      : 575
채널 수      : 7
직무 분야 수 : 6
posting_id 중복: 0
채널별: hrmos 92 / talentio 92 / geekly 85 / company_site 79 / doda 78 / openwork 76 / mid_tenshoku 73
스킬 상위 5: SQL 326 / Requirement definition 324 / Python 309 / AWS 290 / GCP 290
```

- **Streamlit** `streamlit run app/dashboard.py` — 첫 화면 데이터셋 택1, 일본어 트랙: 요약→직무 수요→스킬 신호→채널→표준화 품질→방법 (캡처 03·04·05)
- **SQL 조회** `python cloud/query_marts.py` — `jdf.postings_canonical` COUNT + 상위 10행 + dbt 마트 (코드 있음 · 실클라우드 미실행)

## 4. 부하·장애·복구에서 확인한 것 / 아직 보장 못하는 것

확인한 것 (5차시, `docs/loadtest-logs/evidence.md`, 캡처 17):
- 부하 약 1,284배(20→25,684건)에도 collect 시간 거의 불변 — 카탈로그 전체 순회가 지배 비용
- 같은 `dt=` 파티션 재실행 시 누적 안 됨 — CSV `"w"` + parquet `overwrite`가 멱등 보장
- Spark 정규화 강제 중단 → 깨진 출력 없음 → 재실행 1회로 완전 복구

확인함 (클라우드, 2026-09-06 실측):
- **MERGE 멱등성**: `load_to_bq.py` 2회 연속 → 1회차 inserted=575, 2회차 updated=575 inserted=0, `canonical_total` 575 불변
- **alert 가드**: 빈 파티션(0행 parquet) → `staging_rows==0` → raise, MERGE 중단
- **canonical COUNT = spark after**: `jdf.postings_canonical` 575 = Spark 전처리 후 575

아직 보장 못하는 것:
- **ATS 트랙 ↔ synth canonical 스키마 통합**: 두 트랙 컬럼셋이 달라 `postings_canonical` 공유 시 충돌 가능 (synth만 적재함)
- 동시 실행 경합, 실제 DB 적재 실패, Kafka 스트리밍 트랙 장애 재현
- Airflow `push_to_cloud=true` 실제 run (코드만, DAG import 확인까지)

## 클라우드 실행 결과 (2026-09-06)

프로젝트 `bright-link-507313-q3` · 버킷 `gs://bright-link-507313-q3-jdf-raw` · 데이터셋 `jdf` · region `asia-northeast1`.

| 단계 | 결과 | 캡처 |
|---|---|---|
| `cloud/setup.sh` | API 활성화 + 버킷·데이터셋 생성 | 07 |
| `run_pipeline.sh --cloud` | GCS 업로드 1파일 70KB → staging 575 → MERGE inserted 575 → `canonical_total` **575** | 08 |
| MERGE 2회차 | updated 575 / inserted 0 / `canonical_total` **575** (불변, 멱등) | 09 |
| `dbt run` | PASS=3 (`stg_postings` view + `mart_tech_demand`·`mart_platform_dist` table) | 12 |
| `dbt test` | PASS=7 (`posting_id`·`skill`·`source_platform` unique+not_null) | 12 |
| `cloud/query_marts.py` (SQL 서빙) | canonical 575 · mart_tech_demand 7행 (SQL 326 / 요건정의 324 / Python 309 / AWS 290 / GCP 290) · mart_platform_dist 7행 (스킬 태그율 0.96~1.0) | 10 |
| Looker Studio | [리포트 링크](https://lookerstudio.google.com/reporting/a69e9404-fea5-44cd-ac55-efc26c06720c) — 스코어카드 5 + 직무×경력 누적막대 + 스킬 수요 막대, 전부 BigQuery dbt 마트 직결 | 14 |
| Public ATS → BigQuery | `jdf.ats_postings` 25,684행 + dbt ATS 마트 5종 (`dbt test` PASS=17) | — |
| alert 가드 | 빈 파티션 → `staging_rows==0` → raise | 16 |

**BigQuery `canonical_total` 575 = 로컬 Spark 전처리 후 575 = `read_result.py` 575** — 로컬↔클라우드 건수 일치.

## 6. 남은 문제와 다음 단계

1. ~~`cloud/setup.sh` → `run_pipeline.sh --cloud` → `dbt run/test`~~ **2026-09-06 실행 완료** (아래 클라우드 결과). 남은 건 Airflow `push_to_cloud` run
2. ~~Looker Studio 연결~~ **완료** — 리포트 [링크](https://lookerstudio.google.com/reporting/a69e9404-fea5-44cd-ac55-efc26c06720c) + 5페이지 설계 문서 `looker-bi-design.md`. Airflow `push_to_cloud` run 만 남음
3. 합성 데이터 리얼리티: 厚労省 job tag 분포, 섹션 템플릿 풀 30~50개, 볼륨 상향
4. 직무 taxonomy 매핑 · salary 텍스트 파서 (Canonical Schema 전체 매핑)
5. 크론 스케줄 등록 (현재 `airflow dags test` 수동 트리거)

## 확인 방법 (명령 모음)

```bash
bash scripts/run_pipeline.sh            # 단계별 건수 표 (2회 연속 → 동일)
bash scripts/run_pipeline.sh            # 멱등 재현
python scripts/read_result.py           # 서빙: 최종 parquet 읽기
python app/test_dashboard.py            # 집계 로직 자체 검증
# 클라우드 (사용자 지시 시에만):
bash cloud/setup.sh
bash scripts/run_pipeline.sh --cloud
cd dbt && dbt run --profiles-dir . && dbt test --profiles-dir .
python cloud/query_marts.py
```
