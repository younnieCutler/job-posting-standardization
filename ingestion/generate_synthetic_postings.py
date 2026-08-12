"""Generate synthetic Japanese job postings for job-data-foundry ingestion-volume testing.

Two-layer generation: role axis (job family / company / tier, drawn independently of
the golden set) x pattern axis (field-name / salary-type / coverage-gap / tier-blend,
reverse-engineered from docs/golden-set/real-postings-golden-set.csv).

Usage: python ingestion/generate_synthetic_postings.py
Output: data/synthetic/source_a.csv, source_b.csv, source_c.csv, ground_truth.csv
"""
import csv
import random
from pathlib import Path

from faker import Faker

from synth_rules import (
    BLOCKED_COMPANY_NAMES,
    COVERAGE_GAP_RATE,
    EMPLOYMENT_TYPE,
    FIELD_NAME_VARIANTS,
    JOB_FAMILY_GROUPS,
    PREFERRED_REQUIREMENT_POOL,
    SALARY_BANDS_MAN_YEN,
    SALARY_TYPE_FORMATS,
    SENIORITY_TIERS,
    TIER_BLEND_NEIGHBORS,
    TIER_BLEND_RATE,
    TIER_THRESHOLD_PHRASES,
)

N_ROLES = 160
N_NEGATIVE = 15
SEED = 42

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "synthetic"

SOURCE_A_FIELDS = [
    "job_title", "company_name", "salary_range_text", "description_text",
    "requirements_text", "preferred_text", "employment_type", "posting_id",
]
SOURCE_B_FIELDS = [
    "position_name", "employer", "comp_text", "duties_text",
    "must_have_text", "nice_to_have_text", "emp_type", "posting_ref",
]
SOURCE_C_FIELDS = ["company", "description_blob", "ref_id"]

GROUND_TRUTH_FIELDS = [
    "role_id", "posting_id", "source", "job_family_group", "title", "seniority_tier",
    "company", "salary_min", "salary_max", "salary_type",
    "is_negative_control", "tier_blended", "coverage_gap_applied",
]


def make_unique_company(fake, used):
    while True:
        name = fake.company()
        if name not in used and name not in BLOCKED_COMPANY_NAMES:
            used.add(name)
            return name


def build_role_catalog(fake, n_roles, used_companies):
    roles = []
    for role_id in range(n_roles):
        # pick the group first (not a flat pool of all titles) so every group gets
        # roughly equal representation regardless of how many titles it lists
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
            "seniority_tier": tier,
            "company": make_unique_company(fake, used_companies),
            "salary_min": salary_min,
            "salary_max": salary_max,
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
            "seniority_tier": template["seniority_tier"],
            "company": make_unique_company(fake, used_companies),  # forced different company
            "salary_min": template["salary_min"],
            "salary_max": template["salary_max"],
        })
    return negatives


def render_requirements(role):
    tier = role["seniority_tier"]
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


def make_variant(role, variant_idx, is_negative=False):
    salary_type = random.choice(list(SALARY_TYPE_FORMATS))
    salary_text = SALARY_TYPE_FORMATS[salary_type].format(
        min=role["salary_min"], max=role["salary_max"],
        min_m=round(role["salary_min"] / 12), max_m=round(role["salary_max"] / 12),
    )
    requirements_text, tier_blended = render_requirements(role)
    preferred_lines, coverage_gap_applied = render_preferred(role)
    return {
        "posting_id": f"{role['role_id']}-{variant_idx}",
        "role_id": role["role_id"],
        "company": role["company"],
        "title": role["title"],
        "job_family_group": role["job_family_group"],
        "seniority_tier": role["seniority_tier"],
        "salary_min": role["salary_min"],
        "salary_max": role["salary_max"],
        "salary_type": salary_type,
        "salary_text": salary_text,
        "employment_type": EMPLOYMENT_TYPE,
        "job_description_field_name": random.choice(FIELD_NAME_VARIANTS["job_description"]),
        "requirements_field_name": random.choice(FIELD_NAME_VARIANTS["requirements"]),
        "requirements_text": requirements_text,
        "preferred_field_name": random.choice(FIELD_NAME_VARIANTS["preferred"]),
        "preferred_text": "、".join(preferred_lines),
        "is_negative_control": is_negative,
        "tier_blended": tier_blended,
        "coverage_gap_applied": coverage_gap_applied,
    }


def serialize_source_a(p):
    return {
        "job_title": p["title"],
        "company_name": p["company"],
        "salary_range_text": p["salary_text"],
        "description_text": f"{p['job_description_field_name']}：{p['title']}としてご活躍いただきます。",
        "requirements_text": f"{p['requirements_field_name']}：{p['requirements_text']}",
        "preferred_text": f"{p['preferred_field_name']}：{p['preferred_text']}",
        "employment_type": p["employment_type"],
        "posting_id": p["posting_id"],
    }


def serialize_source_b(p):
    return {
        "position_name": p["title"],
        "employer": p["company"],
        "comp_text": p["salary_text"],
        "duties_text": f"{p['job_description_field_name']}：{p['title']}に関する業務全般。",
        "must_have_text": f"{p['requirements_field_name']}：{p['requirements_text']}",
        "nice_to_have_text": f"{p['preferred_field_name']}：{p['preferred_text']}",
        "emp_type": p["employment_type"],
        "posting_ref": p["posting_id"],
    }


def serialize_source_c(p):
    blob = (
        f"【{p['title']}】{p['company']}\n"
        f"{p['job_description_field_name']}：{p['title']}としてご活躍いただきます。\n"
        f"{p['requirements_field_name']}：{p['requirements_text']}\n"
        f"{p['preferred_field_name']}：{p['preferred_text']}\n"
        f"給与：{p['salary_text']}　雇用形態：{p['employment_type']}"
    )
    return {"company": p["company"], "description_blob": blob, "ref_id": p["posting_id"]}


SERIALIZERS = [
    ("source_a", serialize_source_a, SOURCE_A_FIELDS),
    ("source_b", serialize_source_b, SOURCE_B_FIELDS),
    ("source_c", serialize_source_c, SOURCE_C_FIELDS),
]


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main():
    random.seed(SEED)
    fake = Faker("ja_JP")
    Faker.seed(SEED)
    used_companies = set()

    roles = build_role_catalog(fake, N_ROLES, used_companies)
    negatives = build_negative_roles(fake, N_NEGATIVE, roles, used_companies)

    postings = []
    for role in roles:
        for v in range(random.randint(2, 5)):  # mirrors golden-set group sizes (2,5,7,4)
            postings.append(make_variant(role, v))
    for role in negatives:
        postings.append(make_variant(role, 0, is_negative=True))

    random.shuffle(postings)  # source assignment shouldn't correlate with generation order

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sources = {name: [] for name, _, _ in SERIALIZERS}
    ground_truth_rows = []

    for i, p in enumerate(postings):
        source_name, serializer, _ = SERIALIZERS[i % 3]
        sources[source_name].append(serializer(p))
        ground_truth_rows.append({
            "role_id": p["role_id"], "posting_id": p["posting_id"], "source": source_name,
            "job_family_group": p["job_family_group"], "title": p["title"],
            "seniority_tier": p["seniority_tier"], "company": p["company"],
            "salary_min": p["salary_min"], "salary_max": p["salary_max"],
            "salary_type": p["salary_type"], "is_negative_control": p["is_negative_control"],
            "tier_blended": p["tier_blended"], "coverage_gap_applied": p["coverage_gap_applied"],
        })

    for name, _, fields in SERIALIZERS:
        write_csv(OUT_DIR / f"{name}.csv", sources[name], fields)
    write_csv(OUT_DIR / "ground_truth.csv", ground_truth_rows, GROUND_TRUTH_FIELDS)

    print(f"roles={len(roles)} negatives={len(negatives)} postings={len(postings)}")
    for name, _, _ in SERIALIZERS:
        print(f"{name}: {len(sources[name])} rows")
    print(f"ground_truth: {len(ground_truth_rows)} rows -> {OUT_DIR}")


if __name__ == "__main__":
    main()
