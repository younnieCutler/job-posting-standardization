"""Generate synthetic Japanese job postings for job-data-foundry ingestion-volume testing.

Two-layer generation: role axis (job family / company / tier / location, drawn
independently of the golden set) x pattern axis (field-name / salary-type /
coverage-gap / tier-blend, reverse-engineered from
docs/golden-set/real-postings-golden-set.csv), rendered per real platform
(PLATFORM_PROFILES) instead of anonymous source_a/b/c.

posting_id = sha256(source_platform + source_posting_id) — deterministic, so re-running
the generator with the same SEED reproduces identical IDs (BigQuery MERGE key).

Usage: python ingestion/generate_synthetic_postings.py
Output: data/raw/<platform>/<platform>.parquet (GCS Raw Zone, local emulation)
        data/synthetic/ground_truth.csv (answer key for downstream matching/verify)
"""
import hashlib
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

from synth_rules import (
    BLOCKED_COMPANY_NAMES,
    COVERAGE_GAP_RATE,
    EMPLOYMENT_TYPE,
    FIELD_NAME_VARIANTS,
    JOB_FAMILY_GROUPS,
    LOCATION_POOL,
    PLATFORM_PROFILES,
    PREFERRED_REQUIREMENT_POOL,
    SALARY_BANDS_MAN_YEN,
    SALARY_TYPE_FORMATS,
    SENIORITY_TIERS,
    TIER_BLEND_NEIGHBORS,
    TIER_BLEND_RATE,
    TIER_EXCEPTION_RATE,
    TIER_EXCEPTIONS,
    TIER_THRESHOLD_PHRASES,
)

N_ROLES = 160
N_NEGATIVE = 15
SEED = 42

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"  # GCS Raw Zone stand-in: bucket/<platform>/*.parquet
GROUND_TRUTH_DIR = REPO_ROOT / "data" / "synthetic"

GROUND_TRUTH_FIELDS = [
    "role_id", "posting_id", "source_platform", "job_family_group", "title", "tier",
    "company", "location", "salary_min", "salary_max", "salary_type",
    "is_negative_control", "tier_blended", "coverage_gap_applied",
]


def make_unique_company(fake, used):
    while True:
        name = fake.company()
        if name not in used and name not in BLOCKED_COMPANY_NAMES:
            used.add(name)
            return name


def pick_location():
    return random.choices(list(LOCATION_POOL), weights=list(LOCATION_POOL.values()))[0]


def build_role_catalog(fake, n_roles, used_companies):
    roles = []
    for role_id in range(n_roles):
        group = random.choice(list(JOB_FAMILY_GROUPS))
        title = random.choice(JOB_FAMILY_GROUPS[group])
        tier = random.choice(SENIORITY_TIERS)
        base_min, base_max = SALARY_BANDS_MAN_YEN[tier]
        jitter = random.randint(-30, 30)
        salary_min = max(300, base_min + jitter)
        salary_max = salary_min + random.randint(100, 250)
        roles.append({
            "role_id": str(role_id),
            "job_family_group": group,
            "title": title,
            "tier": tier,
            "company": make_unique_company(fake, used_companies),
            "location": pick_location(),
            "salary_min": salary_min,
            "salary_max": salary_max,
        })
    return roles


def build_tier_exception_roles(fake, n_roles, used_companies):
    """null/unknown tier roles — separate exception path, not mixed into the normal
    tier/salary-band distribution (2026-08-18 delta 1)."""
    roles = []
    for i in range(n_roles):
        group = random.choice(list(JOB_FAMILY_GROUPS))
        title = random.choice(JOB_FAMILY_GROUPS[group])
        roles.append({
            "role_id": f"tierexc-{i}",
            "job_family_group": group,
            "title": title,
            "tier": random.choice(TIER_EXCEPTIONS),
            "company": make_unique_company(fake, used_companies),
            "location": pick_location(),
            "salary_min": None,
            "salary_max": None,
        })
    return roles


def build_negative_roles(fake, n_negative, roles, used_companies):
    negatives = []
    for i in range(n_negative):
        template = random.choice(roles)  # copy title/salary band -> superficial overlap
        negatives.append({
            "role_id": f"neg-{i}",
            "job_family_group": template["job_family_group"],
            "title": template["title"],
            "tier": template["tier"],
            "company": make_unique_company(fake, used_companies),  # forced different company
            "location": pick_location(),  # independent location, same overlap pattern as golden-set case 5
            "salary_min": template["salary_min"],
            "salary_max": template["salary_max"],
        })
    return negatives


def render_requirements(role):
    tier = role["tier"]
    if tier not in TIER_THRESHOLD_PHRASES:  # null/unknown exception roles
        return "", False
    phrase = random.choice(TIER_THRESHOLD_PHRASES[tier])
    if random.random() < TIER_BLEND_RATE:
        neighbor = TIER_BLEND_NEIGHBORS[tier]
        phrase = f"{phrase}／{random.choice(TIER_THRESHOLD_PHRASES[neighbor])}"
        return phrase, True
    return phrase, False


def render_preferred(role):
    lines = random.sample(PREFERRED_REQUIREMENT_POOL, k=random.randint(2, 4))
    gap_applied = False
    if random.random() < COVERAGE_GAP_RATE and len(lines) > 1:
        lines = lines[: max(1, len(lines) - random.randint(1, 2))]
        gap_applied = True
    return lines, gap_applied


def make_variant(role, variant_idx, platform, is_negative=False):
    if role["salary_min"] is None:
        salary_type, salary_text = "", ""
    else:
        salary_type = random.choice(list(SALARY_TYPE_FORMATS))
        salary_text = SALARY_TYPE_FORMATS[salary_type].format(
            min=role["salary_min"], max=role["salary_max"],
            min_m=round(role["salary_min"] / 12), max_m=round(role["salary_max"] / 12),
        )
    requirements_text, tier_blended = render_requirements(role)
    preferred_lines, coverage_gap_applied = render_preferred(role)

    profile = PLATFORM_PROFILES[platform]
    source_posting_id = f"{platform}-{role['role_id']}-{variant_idx}"
    posting_id = hashlib.sha256(f"{platform}{source_posting_id}".encode()).hexdigest()

    if random.random() < profile["posted_at_rate"]:
        posted_at = (date(2026, 1, 1) + timedelta(days=random.randint(0, 230))).isoformat()
    else:
        posted_at = None
    agency = "エージェント経由" if random.random() < profile["agency_rate"] else None
    if random.random() < profile["salary_blank_rate"]:
        salary_text = ""  # platform-side omission, independent of tier-exception blanks

    return {
        "posting_id": posting_id,
        "source_posting_id": source_posting_id,
        "source_platform": platform,
        "role_id": role["role_id"],
        "company_name": role["company"],
        "raw_title": role["title"],
        "job_family_group": role["job_family_group"],
        "tier": role["tier"],
        "location_raw": f"{random.choice(FIELD_NAME_VARIANTS['location'])}：{role['location']}",
        "location": role["location"],
        "salary_min": role["salary_min"],
        "salary_max": role["salary_max"],
        "salary_type": salary_type,
        "salary_text": salary_text,
        "employment_type": EMPLOYMENT_TYPE,
        "agency": agency,
        "posted_at": posted_at,
        "description_raw": (
            f"{random.choice(FIELD_NAME_VARIANTS['job_description'])}："
            f"{role['title']}としてご活躍いただきます。"
        ),
        "requirements_raw": (
            f"{random.choice(FIELD_NAME_VARIANTS['requirements'])}：{requirements_text}"
        ),
        "preferred_raw": (
            f"{random.choice(FIELD_NAME_VARIANTS['preferred'])}：{'、'.join(preferred_lines)}"
        ),
        "is_negative_control": is_negative,
        "tier_blended": tier_blended,
        "coverage_gap_applied": coverage_gap_applied,
    }


def main():
    random.seed(SEED)
    fake = Faker("ja_JP")
    Faker.seed(SEED)
    used_companies = set()

    n_tier_exceptions = max(1, round(N_ROLES * TIER_EXCEPTION_RATE))
    roles = build_role_catalog(fake, N_ROLES, used_companies)
    roles += build_tier_exception_roles(fake, n_tier_exceptions, used_companies)
    negatives = build_negative_roles(fake, N_NEGATIVE, roles, used_companies)

    platforms = list(PLATFORM_PROFILES)
    postings = []
    for role in roles:
        for v in range(random.randint(2, 5)):  # mirrors golden-set group sizes
            platform = random.choice(platforms)
            postings.append(make_variant(role, v, platform))
    for role in negatives:
        platform = random.choice(platforms)
        postings.append(make_variant(role, 0, platform, is_negative=True))

    random.shuffle(postings)

    rows_by_platform = {p: [] for p in platforms}
    ground_truth_rows = []
    for p in postings:
        rows_by_platform[p["source_platform"]].append(p)
        ground_truth_rows.append({
            "role_id": p["role_id"], "posting_id": p["posting_id"],
            "source_platform": p["source_platform"],
            "job_family_group": p["job_family_group"], "title": p["raw_title"],
            "tier": p["tier"], "company": p["company_name"], "location": p["location"],
            "salary_min": p["salary_min"], "salary_max": p["salary_max"],
            "salary_type": p["salary_type"], "is_negative_control": p["is_negative_control"],
            "tier_blended": p["tier_blended"], "coverage_gap_applied": p["coverage_gap_applied"],
        })

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for platform, rows in rows_by_platform.items():
        platform_dir = RAW_DIR / platform
        platform_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_parquet(platform_dir / f"{platform}.parquet", index=False)

    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(ground_truth_rows, columns=GROUND_TRUTH_FIELDS).to_csv(
        GROUND_TRUTH_DIR / "ground_truth.csv", index=False, encoding="utf-8-sig",
    )

    print(f"roles={len(roles)} negatives={len(negatives)} postings={len(postings)}")
    for platform, rows in rows_by_platform.items():
        print(f"{platform}: {len(rows)} rows -> {RAW_DIR / platform}")
    print(f"ground_truth: {len(ground_truth_rows)} rows -> {GROUND_TRUTH_DIR}")


if __name__ == "__main__":
    main()
