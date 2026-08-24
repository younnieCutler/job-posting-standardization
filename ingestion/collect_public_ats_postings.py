"""Collect IT postings from public employer ATS APIs without HTML scraping.

Usage: python ingestion/collect_public_ats_postings.py
"""
import argparse
import csv
import hashlib
import html
import json
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

IT_KEYWORDS = (
    "engineer", "engineering", "developer", "software", "data", "analytics",
    "machine learning", "cloud", "security", "infra", "infrastructure", "sre",
    "エンジニア", "開発", "データ", "機械学習", "クラウド", "セキュリティ",
    "インフラ", "情報システム", "プロダクト",
)
FIELDS = (
    "source_platform", "source_posting_id", "company_name", "title", "source_url",
    "location", "department", "description", "source_record_sha256", "collected_at",
)
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BOARDS = ROOT / "data" / "golden-set" / "public-ats-boards.csv"
DEFAULT_OUTPUT = ROOT / "data" / "golden-set" / "public-it-postings.csv"
DEFAULT_MANIFEST = ROOT / "data" / "golden-set" / "public-it-postings-manifest.json"


def text(value):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()


def make_record(platform, posting_id, company, title, url, location, departments, description):
    department = ", ".join(item.get("name", "") for item in departments)
    record = {
        "source_platform": platform,
        "source_posting_id": str(posting_id),
        "company_name": company,
        "title": text(title),
        "source_url": url,
        "location": text(location),
        "department": text(department),
        "description": text(description),
    }
    record["source_record_sha256"] = hashlib.sha256(
        "\x1f".join(record.values()).encode("utf-8")
    ).hexdigest()
    record["search_text"] = " ".join(record[key] for key in ("title", "department", "description"))
    return record


def greenhouse_record(job, company):
    return make_record(
        "greenhouse", job["id"], company, job["title"], job["absolute_url"],
        job.get("location", {}).get("name", ""), job.get("departments", []), job.get("content", ""),
    )


def is_it_record(record):
    searchable = record["search_text"].lower()
    return any(keyword in searchable for keyword in IT_KEYWORDS)


def prepare_records(records, limit=None, seed=None):
    rows = list({
        (row["source_platform"], row["source_posting_id"]): row for row in records
    }.values())
    if limit is not None and limit < len(rows):
        random.Random(seed).shuffle(rows)
        rows = rows[:limit]
    return sorted(rows, key=lambda row: (row["source_platform"], row["source_posting_id"]))


def smartrecruiters_record(job, company):
    return make_record(
        "smartrecruiters", job["id"], company, job.get("name", ""), job.get("ref", ""),
        job.get("location", {}).get("city", ""), [{"name": job.get("department", {}).get("label", "")}],
        job.get("jobAd", {}).get("sections", {}).get("jobDescription", {}).get("text", ""),
    )


def board_url(board):
    if board["ats"] == "greenhouse":
        return f"https://boards-api.greenhouse.io/v1/boards/{board['board']}/jobs?content=true"
    if board["ats"] == "smartrecruiters":
        return f"https://api.smartrecruiters.com/v1/companies/{board['board']}/postings?limit=100"
    raise ValueError(f"unsupported ATS: {board['ats']}")


def fetch_json(url):
    request = Request(url, headers={"User-Agent": "job-posting-standardization/1.0"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def parse_board(board, payload):
    if board["ats"] == "greenhouse":
        return [greenhouse_record(job, board["company"]) for job in payload["jobs"]]
    return [smartrecruiters_record(job, board["company"]) for job in payload["content"]]


def collect_board_records(board, fetch_json=fetch_json):
    try:
        records = parse_board(board, fetch_json(board_url(board)))
        return [record for record in records if is_it_record(record)], None
    except (OSError, ValueError, KeyError) as error:
        return [], str(error)


def read_boards(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_output(records, output, manifest, failures, boards, limit, seed):
    output.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    for record in records:
        record["collected_at"] = now
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    manifest.write_text(json.dumps({
        "collected_at": now, "boards_attempted": len(boards), "records_written": len(records),
        "limit": limit, "seed": seed, "failures": failures,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boards", type=Path, default=DEFAULT_BOARDS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    boards, records, failures = read_boards(args.boards), [], {}
    for index, board in enumerate(boards):
        if index:
            time.sleep(1)
        found, failure = collect_board_records(board)
        records.extend(found)
        if failure:
            failures[f"{board['ats']}:{board['board']}"] = failure
    write_output(prepare_records(records, args.limit, args.seed), args.output, args.manifest,
                 failures, boards, args.limit, args.seed)
    print(f"wrote {len(prepare_records(records, args.limit, args.seed))} records; failures={len(failures)}")


if __name__ == "__main__":
    main()
