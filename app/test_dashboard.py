"""dashboard.py 집계 로직 자체 검증 (프레임워크 없음, assert).

원칙: 측정 가능한 것만 검증. 하드코딩된 "표준화 −N" 지표 없음.
실행: python app/test_dashboard.py
"""
import pandas as pd

from dashboard import (
    ATS_TEXT_COLS,
    SYNTH_TEXT_COLS,
    company_skill_matrix,
    field_level_counts,
    skill_keyword_counts,
    synth_quality,
    top_counts,
)


def _synth() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "posting_id": list("abcd"),
            "company_name": ["X社", "X社", "Y社", "Z社"],
            "source_platform": ["hrmos", "hrmos", "doda", "geekly"],
            "job_family_group": ["data_ai", "data_ai", "software_development", "security_qa"],
            "tier": ["mid", "senior", "junior", "lead"],
            "raw_title": ["データエンジニア", "データエンジニア", "Ｗｅｂエンジニア", "セキュリティエンジニア"],
            "raw_title_normalized": ["データエンジニア", "データエンジニア", "Webエンジニア", "セキュリティエンジニア"],
            "salary_type": ["年俸制", "月給+賞与制", "月給制", ""],
            "preferred_raw": [
                "歓迎要件：Python実務経験、SQL実務経験",
                "尚可条件：パイソン実務経験",       # 표기 변형 → Python 하나로
                "求める経験・スキル：AWSまたはGCP実務経験",
                "歓迎要件：セキュリティ経験",
            ],
            "requirements_raw": ["応募資格：実務経験3年以上"] * 4,
            "description_raw": [""] * 4,
        }
    )


def _ats() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_platform": ["greenhouse", "greenhouse", "ashby"],
            "company_name": ["Acme", "Acme", "Globex"],
            "title": ["Backend Engineer", "Data Engineer", "Backend Engineer"],
            "location": ["San Francisco", "San Francisco", None],
            "description": ["python and sql", "spark, python", "golang"],
            "description_normalized": ["", "", ""],
        }
    )


def test_skill_keywords_fold_spelling_variants():
    got = dict(zip(*skill_keyword_counts(_synth(), SYNTH_TEXT_COLS).values.T))
    assert got["Python"] == 2, got          # "Python" + "パイソン" → 1개 키워드
    assert got["SQL"] == 1 and got["AWS"] == 1 and got["GCP"] == 1, got
    assert "Java" not in got, got


def test_top_counts():
    got = dict(zip(*top_counts(_synth()["source_platform"], 10, "channel").values.T))
    assert got == {"hrmos": 2, "doda": 1, "geekly": 1}, got
    loc = top_counts(_ats()["location"], 5, "location")
    assert loc.iloc[0]["location"] == "San Francisco" and loc.iloc[0]["postings"] == 2


def test_field_level_counts():
    m = field_level_counts(_synth())
    assert m.loc["data_ai", "mid"] == 1 and m.loc["data_ai", "senior"] == 1, m


def test_synth_quality_only_measures_real_things():
    q = synth_quality(_synth())
    assert q["total"] == 4, q
    assert q["nfkc"] == 1, q                # Ｗｅｂ → Web 한 건
    assert q["dup"] == 0, q
    assert q["salary_fmt"] == 4, q          # 측정값 그대로 (年俸制/月給+賞与制/月給制/"")
    assert q["field_variants"] == 3, q      # 존재 종수. "합쳐졌다"고 주장하지 않음
    assert list(q["nulls"].columns) == ["column", "rate"], q["nulls"].columns


def test_ats_skill_keywords_and_company_matrix():
    kw = dict(zip(*skill_keyword_counts(_ats(), ATS_TEXT_COLS).values.T))
    assert kw["Python"] == 2 and kw["SQL"] == 1 and kw["Spark"] == 1 and kw["Go"] == 1, kw
    csm = company_skill_matrix(_ats(), ATS_TEXT_COLS, top_companies=2)
    acme_py = csm[(csm.company == "Acme") & (csm.skill == "Python")]
    assert not acme_py.empty and int(acme_py.iloc[0]["postings"]) == 2, csm


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all passed")
