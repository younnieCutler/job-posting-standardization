# 5차시 과제 증거 요약 — 부하·장애·복구 실험 (2026-08-30)

대상: `ingestion/collect_public_ats_postings.py` → `ingestion/spark_normalize_public_postings.py` (4차시에서 만든 collect→normalize 파이프라인, 코드 무수정, 파라미터만 바꿔 재실행)

실행 환경: `.venv-airflow`(Python 3.13, pyspark 3.5.1), 로컬 macOS, 카탈로그 334~340개 보드(Greenhouse/Ashby) 순차 스캔.

## 1. 베이스라인 (정상 실행 기준치)

```bash
python ingestion/collect_public_ats_postings.py --run-date 2026-08-30-baseline --companies 5 --limit 20
python ingestion/spark_normalize_public_postings.py --run-date 2026-08-30-baseline
```

| 항목 | 값 |
|---|---|
| 입력 | companies=5, limit=20 |
| collect 실행시간 | 3m26.038s |
| 수집 건수 | 20건 (failures=5) |
| normalize 실행시간 | 6.832s |
| Spark 전/후 건수 | 20 → 20 |

로그: `1-baseline-collect.log`, `1-baseline-normalize.log`

## 2. 부하 증가

```bash
python ingestion/collect_public_ats_postings.py --run-date 2026-08-30-scaleup --companies 300
python ingestion/spark_normalize_public_postings.py --run-date 2026-08-30-scaleup
```

| 항목 | 값 |
|---|---|
| 입력 | companies=300 (limit 없음, 기본값) |
| collect 실행시간 | 3m18.872s |
| 수집 건수 | 25,684건 (failures=5, 전부 대상 회사에 공개 보드 없음/404) |
| normalize 실행시간 | 8.322s |
| Spark 전/후 건수 | 25,684 → 25,684 |

건수는 20건→25,684건(약 1,284배)으로 늘었지만 collect 실행시간은 베이스라인과 거의 같음(둘 다 카탈로그 전체 334~340개 보드를 순회하는 게 지배적 비용이고, `--companies`는 순회 후 선택 단계에만 영향). 대신 normalize(Spark) 단계는 20건 6.8초 → 25,684건 8.3초로 데이터량 증가가 직접 반영됨.

로그: `2-scaleup-collect.log`, `2-scaleup-normalize.log`

## 3. 장애 재현 — 동일 이벤트 중복 실행

같은 `--run-date`(`2026-08-30-dup`)로 collect→normalize를 두 번 연속 실행.

```bash
python ingestion/collect_public_ats_postings.py --run-date 2026-08-30-dup --companies 5 --limit 20   # 1회차
python ingestion/spark_normalize_public_postings.py --run-date 2026-08-30-dup                          # 1회차
python ingestion/collect_public_ats_postings.py --run-date 2026-08-30-dup --companies 5 --limit 20   # 2회차 (중복 실행)
python ingestion/spark_normalize_public_postings.py --run-date 2026-08-30-dup                          # 2회차
```

| 회차 | collect 결과 | normalize 결과(before→after) |
|---|---|---|
| 1회차 | `wrote 20 records; companies=5; failures=6; run_date=2026-08-30-dup` | 20 → 20 |
| 2회차 | `wrote 20 records; companies=5; failures=5; run_date=2026-08-30-dup` | 20 → 20 |

**결과**: 같은 파티션(`dt=2026-08-30-dup`)에 두 번 실행해도 데이터가 40건으로 누적되지 않고 20건 그대로 유지됨 — collect의 CSV `"w"` 모드 덮어쓰기 + normalize의 parquet `mode("overwrite")`가 같은 `dt` 파티션 재실행을 자연스럽게 멱등(idempotent)으로 만들어줌. `posting_id = sha256(source_platform+source_posting_id)` dedup은 한 실행 내부 중복 제거용이고, 재실행 간 중복 방지는 파티션 덮어쓰기가 담당.

로그: `3-duplicate-run1-collect.log`, `3-duplicate-run1-normalize.log`, `3-duplicate-run2-collect.log`, `3-duplicate-run2-normalize.log`, manifest 비교: `3-duplicate-run1-manifest.json` vs `3-duplicate-run2-manifest.json` (차이는 `collected_at` 타임스탬프와 그때그때 다른 네트워크 실패 1건뿐 — 레코드 수는 동일)

## 4. 장애 재현 — 잘못된 입력

```bash
python ingestion/collect_public_ats_postings.py --run-date 2026-08-30-badinput \
  --catalog-url "https://raw.githubusercontent.com/ConorsCode/open-jobs-data/main/companies-nonexistent.json"
```

결과: `urllib.error.HTTPError: HTTP Error 404: Not Found` — `fetch_json()`에서 즉시 예외 발생, exit code 1. `data/golden-set/public-it-postings/dt=2026-08-30-badinput/` 디렉토리 자체가 생성되지 않음(부분 파일 없음) — `write_output()`이 카탈로그 fetch 성공 이후에만 호출되므로 실패 시 깨끗하게 멈춤.

로그: `4-bad-input.log` (트레이스백 전문)

## 5. 장애 재현 — 처리 작업 강제 중단 + 복구

scaleup 파티션(25,684건)을 복제한 `dt=2026-08-30-interrupt-test`에 대해 Spark 정규화를 `timeout 3`으로 강제 종료(정상 소요시간 8.3초 중 3초 지점에서 kill).

```bash
timeout 3 python ingestion/spark_normalize_public_postings.py --run-date 2026-08-30-interrupt-test   # 강제 중단
python ingestion/spark_normalize_public_postings.py --run-date 2026-08-30-interrupt-test              # 복구 재실행
```

| 단계 | 결과 |
|---|---|
| 강제 중단 (exit 124) | 출력 디렉토리에 파일 0개 (Spark가 `write.parquet()` 완료 전 kill되어 부분 파일 없음, `df.write.mode("overwrite")`는 임시 디렉토리에 쓰고 커밋하는 방식이라 중단 시 깨진 parquet이 남지 않음) |
| 복구 재실행 (exit 0) | `before=25684 after=25684 saved_to=.../dt=2026-08-30-interrupt-test` — `_SUCCESS` 마커 존재, 정상 완료 |

**결과**: 처리 도중 강제 종료돼도 손상된 출력이 남지 않고, 같은 명령을 다시 실행하면 원본 건수(25,684건) 그대로 완전히 복구됨 — 유실도 중복도 없음.

로그: `5-interrupted.log`, `5-recovered.log`

## 스코프 밖

- DB 적재 실패 재현 — 이 파이프라인엔 로컬 파일 emulation만 있고 실제 DB 연결이 없어 해당 없음.
- k6/Artillery/Locust/Toxiproxy — HTTP API·DB 커넥션이 있는 파이프라인 대상 도구라 이 배치 트랙에는 불필요해 사용하지 않음.
- Kafka 스트리밍 트랙(4차시 별도 제출분)의 장애 재현 — 이번 실험은 배치 트랙에 집중, 시간 관계상 다루지 않음.
