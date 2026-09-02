"""dashboard.py 집계 로직 자체 검증 (프레임워크 없음, assert).

실행: python app/test_dashboard.py
"""
import pandas as pd

from dashboard import (
    count_skills,
    normalization_before_after,
    platform_distribution,
    salary_bands,
    salary_type_dist,
)


def _sample() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "posting_id": list("abcd"),
            "company_name": ["X社", "X社", "Y社", "Z社"],
            "source_platform": ["hrmos", "hrmos", "doda", "geekly"],
            "job_family_group": ["data_ai", "data_ai", "software_development", "security_qa"],
            "tier": ["mid", "senior", "junior", "lead"],
            "raw_title": ["データエンジニア", "データエンジニア", "Webエンジニア", "セキュリティエンジニア"],
            "raw_title_normalized": ["データエンジニア", "データエンジニア", "Webエンジニア", "セキュリティエンジニア"],
            "salary_min": [500, 700, 350, 800],
            "salary_max": [750, 1000, 500, 1100],
            "salary_type": ["年俸制", "月給+賞与制", "月給制", "年俸制"],
            "preferred_raw": [
                "歓迎要件：Python実務経験、SQL実務経験",
                "尚可条件：パイソン実務経験",  # 표기 변형 — python 으로 합산돼야
                "求める経験・スキル：AWSまたはGCP実務経験",
                "歓迎要件：セキュリティ経験",
            ],
            "requirements_raw": ["応募資格：実務経験3年以上"] * 4,
            "description_raw": [""] * 4,
        }
    )


def test_count_skills_merges_notation_variants():
    got = dict(zip(*count_skills(_sample()).values.T))
    assert got["python"] == 2, got          # "Python" + "パイソン" → python 1개로 합산
    assert got["sql"] == 1 and got["aws"] == 1 and got["gcp"] == 1, got
    assert got["security"] == 1, got
    assert "java" not in got, got


def test_platform_distribution():
    got = dict(zip(*platform_distribution(_sample()).values.T))
    assert got == {"hrmos": 2, "doda": 1, "geekly": 1}, got


def test_salary_bands():
    b = salary_bands(_sample())
    da = b[(b.job_family_group == "data_ai")]
    assert set(da.tier) == {"mid", "senior"}, da.tier.tolist()
    mid = da[da.tier == "mid"].iloc[0]
    assert mid.band_min == 500 and mid.band_max == 750, mid.to_dict()


def test_salary_type_dist():
    got = dict(zip(*salary_type_dist(_sample()).values.T))
    assert got == {"年俸制": 2, "月給+賞与制": 1, "月給制": 1}, got


def test_normalization_before_after():
    nba = normalization_before_after(_sample())
    row = {r.row: (r.before, r.after) for r in nba.itertuples()}
    assert row["field"] == (3, 1), row      # 歓迎要件/尚可条件/求める経験・スキル → 1
    assert row["salary"] == (3, 1), row     # 3 표기 방식 → 1 정규 스키마
    assert row["title"][1] == 3, row        # raw_title_normalized distinct == 3


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all passed")
