"""Collect IT postings from public employer ATS APIs without HTML scraping."""
import hashlib
import html
import re

IT_KEYWORDS = (
    "engineer", "engineering", "developer", "software", "data", "analytics",
    "machine learning", "cloud", "security", "infra", "infrastructure", "sre",
    "エンジニア", "開発", "データ", "機械学習", "クラウド", "セキュリティ",
    "インフラ", "情報システム", "プロダクト",
)


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
