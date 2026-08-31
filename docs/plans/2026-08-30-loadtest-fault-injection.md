# 부하·장애·복구 실험 계획 (5차시 과제)

**Goal:** 지금 있는 ATS 수집기 + Spark 정규화 파이프라인(4차시)을 대상으로 (1) 정상 실행 기준치 기록 (2) 부하 증가 시 처리 시간·건수·오류 기록 (3) 실제 있을 법한 장애 재현 (4) 장애 복구 후 데이터 무결성(유실/중복 없음) 확인. 마감 2026-08-31(월) 17:00.

**Context:** DB 적재/HTTP API/Kafka 스트리밍은 이 트랙에 없음(로컬 파일 emulation만) → 공식 진행 방법 예시 중 "파일·배치 파이프라인" 방식(날짜/건수 범위 확대) 적용. k6/Artillery/Locust/Toxiproxy는 HTTP API·DB 커넥션이 있는 파이프라인용이라 이 트랙엔 해당 없음.

**대상**: `ingestion/collect_public_ats_postings.py` → `ingestion/spark_normalize_public_postings.py` (4차시에서 만든 collect→normalize 파이프라인, 코드 무수정 원칙 — 파라미터만 바꿔 재실행)

## Task 1: 베이스라인 기록

- [x] `--companies 5 --limit 20` 실행, 실행시간(`time`)·수집건수·Spark 전/후 건수 기록 → `docs/loadtest-logs/1-baseline-collect.log`, `docs/loadtest-logs/1-baseline-normalize.log`

## Task 2: 부하 증가

- [x] `--companies 300`(기본값, 전체 카탈로그) 실행, 시간·건수·오류(manifest failures) 기록 → `docs/loadtest-logs/2-scaleup-collect.log`, `2-scaleup-normalize.log`

## Task 3: 장애 재현 (3종)

- [x] **동일 이벤트 중복 실행**: 같은 `--run-date`로 collect→normalize 두 번 연속 실행, `posting_id` 기준 dedup이 중복을 막는지 확인 → `3-duplicate-run-1.log`, `3-duplicate-run-2.log`
- [x] **잘못된 입력**: 존재하지 않는 `--catalog-url`로 실행, 실패 양상(예외/트레이스백) 기록 → `4-bad-input.log`
- [x] **처리 작업 강제 중단**: Spark 정규화 도중 `timeout`으로 강제 종료, 이후 정상 재실행으로 복구되는지 확인 → `5-interrupted.log`, `5-recovered.log`

## Task 4: 복구 검증

- [x] 각 장애 케이스마다 정상 재실행 후 before/after 건수, 파티션 상태 재확인. 유실·중복 없음을 로그로 증명.

## Task 5: README §5차시 섹션 + 발표 자료

- [x] README에 "5차시 과제 — 부하·장애·복구 실험" 섹션 추가 (실행명령, 결과표, 실제구현 vs 계획)
- [x] vault에 큐카드+대본 (기존 워크플로우 그대로)

## 스코프 밖

- DB 적재 실패 재현 — 로컬 emulation이라 실제 DB 연결 없음, 해당 없음
- k6/Artillery/Locust/Toxiproxy 도입 — HTTP API/DB 커넥션 없는 파일 배치 트랙이라 불필요
- Kafka 스트리밍 트랙(4차시 별도 제출분)의 장애 재현 — 이번엔 손대지 않음, 시간 되면 추가 검토

## Status: all 5 tasks complete (2026-08-30).
