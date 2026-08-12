"""Self-check: assert the generated synthetic dataset (data/synthetic/ground_truth.csv)
has enough diversity across the role/pattern axes to avoid collapsing onto the golden
set's 3 companies. Run after generate_synthetic_postings.py.

Usage: python ingestion/verify_coverage.py
"""
import csv
from collections import Counter, defaultdict
from pathlib import Path

GT_PATH = Path(__file__).resolve().parent.parent / "data" / "synthetic" / "ground_truth.csv"

ALL_GROUPS = {
    "software_development", "infrastructure_platform", "data_ai",
    "security_qa", "architecture_consulting", "corporate_it_support",
}
EXPECTED_SALARY_TYPES = {"年俸制", "月給+賞与制", "月給制"}

MIN_DISTINCT_COMPANIES = 20
MIN_TITLES_PER_GROUP = 3
MIN_TIER_BLENDED = 5
MIN_NEGATIVE_CONTROLS = 10
MAX_COMPANY_SHARE = 0.15


def main():
    with GT_PATH.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows, f"no rows found in {GT_PATH} — run generate_synthetic_postings.py first"

    companies = Counter(r["company"] for r in rows)
    assert len(companies) >= MIN_DISTINCT_COMPANIES, (
        f"only {len(companies)} distinct companies, need >= {MIN_DISTINCT_COMPANIES}"
    )

    top_company, top_count = companies.most_common(1)[0]
    top_share = top_count / len(rows)
    assert top_share <= MAX_COMPANY_SHARE, (
        f"company '{top_company}' is {top_share:.0%} of all rows "
        f"(cap {MAX_COMPANY_SHARE:.0%}) — role generation collapsed"
    )

    titles_by_group = defaultdict(set)
    for r in rows:
        titles_by_group[r["job_family_group"]].add(r["title"])

    missing_groups = ALL_GROUPS - set(titles_by_group)
    assert not missing_groups, f"job_family_group(s) never generated: {missing_groups}"

    thin_groups = {g: len(t) for g, t in titles_by_group.items() if len(t) < MIN_TITLES_PER_GROUP}
    assert not thin_groups, (
        f"groups with too few distinct titles (< {MIN_TITLES_PER_GROUP}): {thin_groups}"
    )

    salary_types = {r["salary_type"] for r in rows}
    assert salary_types >= EXPECTED_SALARY_TYPES, f"missing salary_type(s): {EXPECTED_SALARY_TYPES - salary_types}"

    tier_blended_count = sum(1 for r in rows if r["tier_blended"] == "True")
    assert tier_blended_count >= MIN_TIER_BLENDED, (
        f"only {tier_blended_count} tier_blended rows, need >= {MIN_TIER_BLENDED}"
    )

    negative_count = sum(1 for r in rows if r["is_negative_control"] == "True")
    assert negative_count >= MIN_NEGATIVE_CONTROLS, (
        f"only {negative_count} negative_control rows, need >= {MIN_NEGATIVE_CONTROLS}"
    )

    print(
        f"OK: {len(rows)} rows, {len(companies)} distinct companies, "
        f"all {len(ALL_GROUPS)} groups covered, "
        f"tier_blended={tier_blended_count}, negative_control={negative_count}"
    )


if __name__ == "__main__":
    main()
