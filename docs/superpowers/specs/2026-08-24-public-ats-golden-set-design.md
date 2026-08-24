# Public ATS Golden Set Collection

## Goal

Collect up to 300 current Japan IT job postings from employer-published ATS APIs. The output supplies real field-variation examples and can be replayed as an arrival stream for the synthetic-data demo.

## Scope

The collector reads only public GET endpoints used by employer career sites:

- Greenhouse Job Board API
- SmartRecruiters Posting API

It does not crawl job-board HTML, submit forms, bypass rate limits, or collect applicant data. A checked-in allowlist identifies employer ATS boards. The collector records a per-source failure and continues with the other sources.

## Inputs and output

`data/golden-set/public-ats-boards.csv` contains one board per line: ATS type, board identifier, and company name. `--limit` defaults to 300. `--seed` controls the random sample.

`data/golden-set/public-it-postings.csv` contains one row per unique source posting. It preserves source identifiers, URL, collection timestamp, title, location, department, description, and a SHA-256 hash of the fetched source record. `data/golden-set/public-it-postings-manifest.json` records the run settings, source counts, failures, and final count.

The collector identifies IT roles with a small Japanese and English keyword set applied to title, department, and description. It deduplicates by `(source_platform, source_posting_id)` before sampling. If fewer than the requested limit exist, it writes every valid record and exits non-zero so the gap is visible.

## Design

One standard-library Python script owns HTTP reads, parsing, filtering, deduplication, sampling, and CSV/manifest output. It uses a conservative request delay and a clear User-Agent. Greenhouse and SmartRecruiters response parsing stays in two small functions because their public response shapes differ. No new dependencies or crawler framework are needed.

The collector only writes its two output files after it has parsed all sources, so a failed run does not leave a partial golden set. The manifest makes incomplete collection explicit.

## Verification

A standard-library `unittest` module uses fixed API-response fixtures to prove that the collector filters IT work, removes duplicate source IDs, samples deterministically, and signals an undersupplied run. Network calls are not part of the test suite.

## Known ceiling

The allowlist is manually maintained because public ATS APIs do not provide a reliable directory of Japan employer boards. Add a board after confirming that it is an employer-owned public career site and its API remains publicly accessible.
