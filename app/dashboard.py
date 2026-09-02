"""6차시 제출용 BI — TechHire Nexus Japan 노동시장 인텔리전스 리포트 (Streamlit).

페르소나: 일본 IT 엔지니어 RPO + HR 데이터 분석 스타트업. 이 화면은 그 회사가
대기업 HR·TA 부서에 구독 판매하는 B2B 시장 분석 리포트다. 표준화 파이프라인의
저장 결과(BigQuery dbt 마트, 없으면 로컬 parquet)를 읽어 시장 수요·급여·경쟁을
답한다.

실행:
    streamlit run app/dashboard.py

BigQuery 사용 시:
    gcloud auth application-default login
    export JDF_BQ_PROJECT=<project-id>       # 없으면 자동으로 로컬 parquet

집계 로직 자체 검증: python app/test_dashboard.py
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from i18n import LANGS, benchmark_rows, make_t

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_PARQUET = REPO_ROOT / "data" / "processed" / "postings_clean.parquet"
BQ_DATASET = "jdf"

# canonical 스킬 태그 -> 본문에서 매칭할 표기 변형(정규식, 대소문자 무시).
SKILL_PATTERNS: dict[str, str] = {
    "python": r"python|パイソン",
    "sql": r"sql|エスキューエル",
    "aws": r"aws|amazon web services|アマゾンウェブサービス",
    "gcp": r"gcp|google cloud",
    "java": r"\bjava\b|ジャバ",
    "typescript": r"typescript|\bts\b|タイプスクリプト",
    "react": r"react|リアクト",
    "go": r"\bgolang\b|go言語|\bゴー\b",
    "kubernetes": r"kubernetes|k8s|クバネティス",
    "docker": r"docker|ドッカー",
    "terraform": r"terraform|テラフォーム",
    "spark": r"spark|スパーク",
    "machine_learning": r"機械学習|マシンラーニング|machine learning|\bml\b",
    "security": r"セキュリティ|security",
    "requirement_definition": r"要件定義|上流工程",
}

PREFERRED_FIELD_VARIANTS = ["歓迎要件", "尚可条件", "求める経験・スキル"]
TEXT_COLS = ["preferred_raw", "requirements_raw", "description_raw"]
TIER_ORDER = ["junior", "mid", "senior", "lead", "principal", "unknown", "null"]


# ---------- 순수 집계 함수 (test_dashboard.py 에서 검증) ----------

def _combined_text(df: pd.DataFrame) -> pd.Series:
    cols = [c for c in TEXT_COLS if c in df.columns]
    if not cols:
        return pd.Series([""] * len(df), index=df.index)
    return df[cols].fillna("").agg(" ".join, axis=1).str.lower()


def count_skills(df: pd.DataFrame) -> pd.DataFrame:
    """공고 본문에서 canonical 스킬 태그별 공고 수 (표기 변형 합산 후)."""
    text = _combined_text(df)
    rows = [
        {"skill": tag, "postings": int(text.str.contains(pat, regex=True, na=False).sum())}
        for tag, pat in SKILL_PATTERNS.items()
    ]
    out = pd.DataFrame(rows)
    return out[out["postings"] > 0].sort_values("postings", ascending=False).reset_index(drop=True)


def platform_distribution(df: pd.DataFrame) -> pd.DataFrame:
    return df["source_platform"].value_counts().rename_axis("platform").reset_index(name="postings")


def group_tier_matrix(df: pd.DataFrame) -> pd.DataFrame:
    m = pd.crosstab(df["job_family_group"], df["tier"])
    cols = [c for c in TIER_ORDER if c in m.columns] + [c for c in m.columns if c not in TIER_ORDER]
    return m[cols]


def salary_bands(df: pd.DataFrame) -> pd.DataFrame:
    """직무군 × 티어별 연봉 밴드 (만엔, 최소–중앙값–최대). 예외 티어(null/unknown) 제외."""
    d = df[df["tier"].isin(["junior", "mid", "senior", "lead", "principal"])].copy()
    d["salary_min"] = pd.to_numeric(d["salary_min"], errors="coerce")
    d["salary_max"] = pd.to_numeric(d["salary_max"], errors="coerce")
    d["salary_mid"] = (d["salary_min"] + d["salary_max"]) / 2
    g = d.groupby(["job_family_group", "tier"], observed=True).agg(
        band_min=("salary_min", "min"),
        band_median=("salary_mid", "median"),
        band_max=("salary_max", "max"),
        n=("salary_mid", "size"),
    ).reset_index()
    g["tier"] = pd.Categorical(g["tier"], TIER_ORDER, ordered=True)
    return g.sort_values(["job_family_group", "tier"]).reset_index(drop=True)


def salary_type_dist(df: pd.DataFrame) -> pd.DataFrame:
    return df["salary_type"].value_counts().rename_axis("salary_type").reset_index(name="count")


def normalization_before_after(df: pd.DataFrame) -> pd.DataFrame:
    """정규화 전(표기 흔들림 종수) vs 후(canonical 종수) — 3개 실제 항목."""
    text = _combined_text(df)
    field_variants = int(sum(text.str.contains(v.lower(), regex=False, na=False).any()
                             for v in PREFERRED_FIELD_VARIANTS))
    raw_titles = int(df["raw_title"].nunique()) if "raw_title" in df.columns else 0
    norm_titles = (int(df["raw_title_normalized"].nunique())
                   if "raw_title_normalized" in df.columns else raw_titles)
    salary_formats = int(df["salary_type"].nunique()) if "salary_type" in df.columns else 0
    return pd.DataFrame(
        {
            "row": ["field", "title", "salary"],
            "before": [field_variants, raw_titles, salary_formats],
            "after": [1, norm_titles, 1],
        }
    )


# ---------- 데이터 로드 ----------

def load_local() -> pd.DataFrame:
    df = pd.read_parquet(LOCAL_PARQUET)
    if "is_negative_control" in df.columns:
        df = df[~df["is_negative_control"].fillna(False).astype(bool)]
    return df.reset_index(drop=True)


def load_bq_marts(project: str) -> dict[str, pd.DataFrame]:
    from google.cloud import bigquery

    client = bigquery.Client(project=project)
    q = lambda sql: client.query(sql).to_dataframe()  # noqa: E731
    return {
        "tech_demand": q(f"SELECT skill, postings FROM `{project}.{BQ_DATASET}.mart_tech_demand` "
                         f"ORDER BY postings DESC"),
        "platform_dist": q(f"SELECT platform, postings FROM `{project}.{BQ_DATASET}.mart_platform_dist` "
                           f"ORDER BY postings DESC"),
    }


# ---------- 화면 ----------

def _kpi_css() -> str:
    return """
    <style>
      .kpi-row{display:flex;gap:14px;flex-wrap:wrap;margin:8px 0 4px}
      .kpi{flex:1;min-width:150px;background:#fff;border:1px solid #e2e0d6;
           border-left:4px solid #0a5246;border-radius:8px;padding:14px 16px}
      .kpi .v{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:1.7rem;
              font-weight:600;color:#0a5246;line-height:1.1}
      .kpi .l{font-size:.8rem;color:#555;margin-top:4px}
      .who{color:#6b6b6b;font-size:.9rem;border-left:3px solid #cdd8d3;
           padding-left:10px;margin:2px 0 10px}
    </style>
    """


def _kpi_card(value: str, label: str) -> str:
    return f'<div class="kpi"><div class="v">{value}</div><div class="l">{label}</div></div>'


def main() -> None:
    import altair as alt
    import streamlit as st

    st.set_page_config(page_title="TechHire Nexus — Market Intelligence", layout="wide")

    lang_label = st.sidebar.radio("Language / 言語 / 언어", list(LANGS.keys()), index=1)
    lang = LANGS[lang_label]
    t = make_t(lang)
    st.markdown(_kpi_css(), unsafe_allow_html=True)

    st.title(t("app_title"))
    st.caption(t("app_subtitle"))

    project = os.environ.get("JDF_BQ_PROJECT", "").strip()
    bq_marts: dict[str, pd.DataFrame] | None = None
    if project:
        try:
            bq_marts = load_bq_marts(project)
            st.caption(t("source_bq", ref=f"{project}.{BQ_DATASET}"))
        except Exception as exc:  # noqa: BLE001 — 대시보드는 어떤 이유든 로컬로 폴백
            st.warning(t("source_local_fallback", err=f"{type(exc).__name__}: {exc}"))
    if bq_marts is None:
        st.caption(t("source_local", ref=str(LOCAL_PARQUET.relative_to(REPO_ROOT))))

    df = load_local()
    nba = normalization_before_after(df)
    unified = int((nba["before"] - nba["after"]).clip(lower=0).sum())

    st.markdown(
        '<div class="kpi-row">'
        + _kpi_card(f"{len(df):,}", t("kpi_postings"))
        + _kpi_card(f"{df['company_name'].nunique():,}", t("kpi_companies"))
        + _kpi_card(f"{df['job_family_group'].nunique()}", t("kpi_families"))
        + _kpi_card(f"{df['source_platform'].nunique()}", t("kpi_platforms"))
        + _kpi_card(f"−{unified}", t("kpi_norm"))
        + "</div>",
        unsafe_allow_html=True,
    )
    st.caption(t("kpi_norm_help"))
    st.divider()

    # 1. 기술 수요
    st.subheader(t("sec1_title"))
    st.markdown(f'<div class="who">{t("sec1_who")}</div>', unsafe_allow_html=True)
    fams = [t("sec1_all")] + sorted(df["job_family_group"].unique())
    pick = st.selectbox(t("sec1_family_filter"), fams)
    sub = df if pick == t("sec1_all") else df[df["job_family_group"] == pick]
    tech = bq_marts["tech_demand"] if bq_marts else count_skills(sub)
    chart = (
        alt.Chart(tech).mark_bar(color="#0a5246").encode(
            x=alt.X("postings:Q", title=t("col_postings")),
            y=alt.Y("skill:N", sort="-x", title=t("col_skill")),
            tooltip=["skill", "postings"],
        ).properties(height=max(200, 26 * len(tech)))
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption(t("sec1_chart"))
    st.divider()

    # 2. 급여 벤치마크
    st.subheader(t("sec2_title"))
    st.markdown(f'<div class="who">{t("sec2_who")}</div>', unsafe_allow_html=True)
    bands = salary_bands(df)
    bands["band_label"] = bands["job_family_group"] + " · " + bands["tier"].astype(str)
    label_order = bands["band_label"].tolist()
    base = alt.Chart(bands)
    band_chart = alt.layer(
        base.mark_bar(opacity=0.35, color="#0a5246").encode(
            x=alt.X("band_min:Q", title=t("sec2_band")),
            x2="band_max:Q",
            y=alt.Y("band_label:N", sort=label_order, title=None),
            tooltip=["job_family_group", "tier", "band_min", "band_median", "band_max", "n"],
        ),
        base.mark_tick(color="#b4471f", thickness=2, size=16).encode(
            x="band_median:Q",
            y=alt.Y("band_label:N", sort=label_order, title=None),
        ),
    ).properties(height=max(240, 22 * len(bands)))
    st.altair_chart(band_chart, use_container_width=True)
    c_a, c_b = st.columns([2, 1])
    with c_a:
        st.dataframe(
            bands.rename(columns={
                "job_family_group": t("col_family"), "tier": t("col_tier"),
                "band_min": t("col_min"), "band_median": t("col_median"),
                "band_max": t("col_max"), "n": t("col_count"),
            }),
            use_container_width=True, hide_index=True,
        )
    with c_b:
        stype = salary_type_dist(df).rename(columns={
            "salary_type": t("col_type"), "count": t("col_count")})
        st.dataframe(stype, use_container_width=True, hide_index=True)
        st.caption(t("sec2_type"))
    st.divider()

    # 3. 경쟁 강도 & 채널
    st.subheader(t("sec3_title"))
    st.markdown(f'<div class="who">{t("sec3_who")}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        heat = group_tier_matrix(df).reset_index().melt(
            id_vars="job_family_group", var_name="tier", value_name="postings")
        h = alt.Chart(heat).mark_rect().encode(
            x=alt.X("tier:N", sort=TIER_ORDER, title=t("col_tier")),
            y=alt.Y("job_family_group:N", title=t("col_family")),
            color=alt.Color("postings:Q", scale=alt.Scale(scheme="teals"), title=t("col_postings")),
            tooltip=["job_family_group", "tier", "postings"],
        )
        st.altair_chart(h, use_container_width=True)
        st.caption(t("sec3_heat"))
    with c2:
        plat = bq_marts["platform_dist"] if bq_marts else platform_distribution(df)
        p = alt.Chart(plat).mark_bar(color="#0a5246").encode(
            x=alt.X("postings:Q", title=t("col_postings")),
            y=alt.Y("platform:N", sort="-x", title=t("col_platform")),
            tooltip=["platform", "postings"],
        )
        st.altair_chart(p, use_container_width=True)
        st.caption(t("sec3_platform"))
    st.divider()

    # 4. 표준화 방법론
    st.subheader(t("sec4_title"))
    st.markdown(f'<div class="who">{t("sec4_who")}</div>', unsafe_allow_html=True)
    label = {"field": t("sec4_row_field"), "title": t("sec4_row_title"), "salary": t("sec4_row_salary")}
    show = pd.DataFrame({
        t("sec4_item"): [label[r] for r in nba["row"]],
        t("sec4_before"): nba["before"],
        t("sec4_after"): nba["after"],
    })
    st.dataframe(show, use_container_width=True, hide_index=True)
    st.info(t("sec4_note"))

    with st.expander(t("sec4_bench_title"), expanded=False):
        bench = pd.DataFrame(benchmark_rows(lang)).rename(
            columns={"name": t("bench_company"), "what": t("bench_what"), "maps": t("bench_maps")}
        )
        st.dataframe(bench, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
