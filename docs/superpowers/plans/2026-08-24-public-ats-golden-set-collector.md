# Public ATS Golden Set Collector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collect all IT postings from 300 employer ATS APIs without HTML scraping.

**Architecture:** A standard-library Python script fetches Greenhouse and SmartRecruiters public JSON, normalizes records, filters IT work, deduplicates, then writes a CSV and manifest. Unit tests inject fixed HTTP payloads.

**Tech Stack:** Python standard library: argparse, csv, hashlib, html, json, random, urllib, unittest.

---

### Task 1: Normalize and filter one ATS record

**Files:**
- Create: `tests/test_collect_public_ats_postings.py`
- Create: `ingestion/collect_public_ats_postings.py`

- [x] Write a failing `unittest` for `greenhouse_record()` where a `Data Engineer` fixture produces `source_platform == "greenhouse"`, `source_posting_id == "7"`, and passes `is_it_record()`.
- [x] Run `python -m unittest tests.test_collect_public_ats_postings -v`; expect an import failure.
- [x] Add `make_record()`, `greenhouse_record()`, and `is_it_record()` using a compact Japanese/English IT keyword tuple.
- [x] Re-run `python -m unittest tests.test_collect_public_ats_postings -v`; expect PASS.
- [x] Commit the test and implementation with `feat: normalize public ATS job records`.

### Task 2: Deduplicate and optionally sample

**Files:**
- Modify: `tests/test_collect_public_ats_postings.py`
- Modify: `ingestion/collect_public_ats_postings.py`

- [x] Write a failing test where three source IDs with one duplicate become two unique rows after `prepare_records(records, limit=2, seed=9)`.
- [x] Run that test; expect missing `prepare_records`.
- [x] Add `prepare_records()` that deduplicates by `(source_platform, source_posting_id)`, and applies a seeded cap only when `limit` is set.
- [x] Re-run the complete test module; expect PASS.
- [x] Commit with `feat: deduplicate public ATS records`.

### Task 3: Fetch allowed boards and write artifacts

**Files:**
- Modify: `tests/test_collect_public_ats_postings.py`
- Modify: `ingestion/collect_public_ats_postings.py`
- Create: `data/golden-set/public-ats-boards.csv`
- Modify: `README.md`

- [x] Write a failing test where a `URLError("offline")` makes `collect_board_records()` return `([], "<error>")` instead of raising.
- [x] Run that test; expect missing `collect_board_records`.
- [x] Add Greenhouse, SmartRecruiters, and Ashby URLs/parsers, a 250ms request delay, `--limit`, `--seed`, `--companies`, and output paths. `main()` records failed boards but returns success after producing available records.
- [x] Load a MIT-licensed public ATS company catalog, select IT postings from the first 300 companies with results, and document the command in README.
- [x] Run `python -m unittest tests.test_collect_public_ats_postings -v` and `python -m py_compile ingestion/collect_public_ats_postings.py`; expect PASS with no compiler output.
- [x] Commit with `feat: collect public ATS golden-set postings`.
