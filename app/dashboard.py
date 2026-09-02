"""6차시 — JDF 채용공고 표준화 리포트 (Streamlit).

원칙:
- 화면은 데이터가 실제로 증명하는 것만 주장한다.
- 두 데이터셋을 합쳐 하나의 시장처럼 보여주지 않는다. 첫 화면에서 하나를 고른다.
  * 일본어 합성 데이터 → 표준화 파이프라인 품질 검증
  * 글로벌 공개 ATS(실제) → 시장 스냅샷 분석
- 개발자용 컬럼명·DB 용어를 화면에 노출하지 않는다. 기술 설명은 도움말에서만.
- 미구현 기능을 완성된 것처럼 표시하지 않는다.
- 차트 제목은 질문형.

실행: streamlit run app/dashboard.py
자체 검증: python app/test_dashboard.py
"""
from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd

from i18n import DATASETS, LANGS, bench_table, make_t, notimpl

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNTH_PARQUET = REPO_ROOT / "data" / "processed" / "postings_clean.parquet"
ATS_ROOT = REPO_ROOT / "data" / "golden-set" / "public-it-postings-canonical"

# 스킬 키워드 -> 본문에서 매칭할 표기 변형(정규식, 대소문자 무시). Skill Taxonomy 아님.
SKILL_KEYWORDS: dict[str, str] = {
    "Python": r"python|パイソン",
    "SQL": r"sql|エスキューエル",
    "AWS": r"aws|amazon web services|アマゾンウェブサービス",
    "GCP": r"gcp|google cloud",
    "Java": r"\bjava\b|ジャバ",
    "TypeScript": r"typescript|\bts\b|タイプスクリプト",
    "React": r"react|リアクト",
    "Go": r"\bgolang\b|go言語|\bゴー\b",
    "Kubernetes": r"kubernetes|k8s|クバネティス",
    "Docker": r"docker|ドッカー",
    "Terraform": r"terraform|テラフォーム",
    "Spark": r"spark|スパーク",
    "ML": r"機械学習|マシンラーニング|machine learning|\bml\b",
    "Security": r"セキュリティ|security",
    "Requirement definition": r"要件定義|上流工程",
}

PREFERRED_FIELD_VARIANTS = ["歓迎要件", "尚可条件", "求める経験・スキル"]
SYNTH_TEXT_COLS = ["preferred_raw", "requirements_raw", "description_raw"]
ATS_TEXT_COLS = ["title", "description", "description_normalized"]
LEVEL_ORDER = ["junior", "mid", "senior", "lead", "principal", "unknown", "null"]


# ---------- 순수 집계 (test_dashboard.py 에서 검증) ----------

def _text(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    use = [c for c in cols if c in df.columns]
    if not use:
        return pd.Series([""] * len(df), index=df.index)
    return df[use].fillna("").agg(" ".join, axis=1).str.lower()


def skill_keyword_counts(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    text = _text(df, cols)
    rows = [
        {"skill": kw, "postings": int(text.str.contains(pat, regex=True, na=False).sum())}
        for kw, pat in SKILL_KEYWORDS.items()
    ]
    out = pd.DataFrame(rows)
    return out[out["postings"] > 0].sort_values("postings", ascending=False).reset_index(drop=True)


def top_counts(series: pd.Series, n: int, name: str) -> pd.DataFrame:
    return (
        series.fillna("(blank)").astype(str).value_counts().head(n)
        .rename_axis(name).reset_index(name="postings")
    )


def field_level_counts(df: pd.DataFrame) -> pd.DataFrame:
    m = pd.crosstab(df["job_family_group"], df["tier"])
    cols = [c for c in LEVEL_ORDER if c in m.columns] + [c for c in m.columns if c not in LEVEL_ORDER]
    return m[cols]


def synth_quality(df: pd.DataFrame) -> dict:
    """실제로 측정 가능한 지표만."""
    total = len(df)
    nfkc = (int((df["raw_title"].fillna("") != df["raw_title_normalized"].fillna("")).sum())
            if {"raw_title", "raw_title_normalized"}.issubset(df.columns) else None)
    dup = int(df["posting_id"].duplicated().sum()) if "posting_id" in df.columns else None
    nulls = (df.isna().mean().sort_values(ascending=False).head(8).round(3)
             .rename_axis("column").reset_index(name="rate"))
    salary_fmt = int(df["salary_type"].nunique(dropna=True)) if "salary_type" in df.columns else None
    text = _text(df, SYNTH_TEXT_COLS)
    field_variants = int(sum(
        text.str.contains(v.lower(), regex=False, na=False).any() for v in PREFERRED_FIELD_VARIANTS
    ))
    return {"total": total, "nfkc": nfkc, "dup": dup, "nulls": nulls,
            "salary_fmt": salary_fmt, "field_variants": field_variants}


def company_skill_matrix(df: pd.DataFrame, cols: list[str], top_companies: int = 8) -> pd.DataFrame:
    top = df["company_name"].value_counts().head(top_companies).index
    sub = df[df["company_name"].isin(top)]
    rows = []
    for comp, g in sub.groupby("company_name"):
        text = _text(g, cols)
        for kw, pat in SKILL_KEYWORDS.items():
            c = int(text.str.contains(pat, regex=True, na=False).sum())
            if c:
                rows.append({"company": comp, "skill": kw, "postings": c})
    return pd.DataFrame(rows)


# ---------- 데이터 로드 (소스 섞지 않음) ----------

def load_synthetic() -> pd.DataFrame:
    df = pd.read_parquet(SYNTH_PARQUET)
    if "is_negative_control" in df.columns:
        df = df[~df["is_negative_control"].fillna(False).astype(bool)]
    return df.reset_index(drop=True)


def list_ats_runs() -> list[str]:
    return sorted({Path(p).parent.name.removeprefix("dt=")
                   for p in glob.glob(str(ATS_ROOT / "dt=*" / "*.parquet"))})


def load_ats(run: str) -> pd.DataFrame:
    return pd.read_parquet(ATS_ROOT / f"dt={run}")


# ---------- 화면 조각 ----------

def _css() -> str:
    return """
    <style>
      .kpi-row{display:flex;gap:14px;flex-wrap:wrap;margin:6px 0}
      .kpi{flex:1;min-width:150px;background:#fff;border:1px solid #e2e0d6;
           border-left:4px solid #0a5246;border-radius:8px;padding:12px 15px}
      .kpi .v{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:1.5rem;
              font-weight:600;color:#0a5246}
      .kpi .l{font-size:.78rem;color:#555;margin-top:3px}
      .frame{color:#555;font-size:.9rem;background:#eef2f0;border-radius:6px;
             padding:8px 12px;margin:4px 0 12px}
    </style>
    """


def _kpi_row(pairs: list[tuple[str, str]]) -> str:
    cells = "".join(
        f'<div class="kpi"><div class="v">{v}</div><div class="l">{l}</div></div>' for v, l in pairs
    )
    return f'<div class="kpi-row">{cells}</div>'


def _frame(st, t, who_key: str, q_key: str) -> None:
    st.markdown(
        f'<div class="frame"><b>{t("who")}:</b> {t(who_key)}<br>'
        f'<b>{t("question")}:</b> {t(q_key)}</div>',
        unsafe_allow_html=True,
    )


def _bar(alt, df, x_title, y_field, y_title, color="#0a5246"):
    return alt.Chart(df).mark_bar(color=color).encode(
        x=alt.X("postings:Q", title=x_title),
        y=alt.Y(f"{y_field}:N", sort="-x", title=y_title),
        tooltip=list(df.columns),
    )


# ---------- JAPAN TRACK ----------

def render_japan(st, alt, t) -> None:
    df = load_synthetic()
    st.warning(t("jp_warning"))

    st.header(t("jp_h_summary"))
    _frame(st, t, "reader_planner", "jp_q_summary")
    st.markdown(_kpi_row([
        (f"{len(df):,}", t("k_jp_records")),
        (f"{df['company_name'].nunique():,}", t("k_jp_companies")),
        (f"{df['source_platform'].nunique()}", t("k_jp_channels")),
        (f"{df['job_family_group'].nunique()}", t("k_jp_fields")),
    ]), unsafe_allow_html=True)
    st.divider()

    st.header(t("jp_h_demand"))
    _frame(st, t, "reader_planner", "jp_q_demand")
    heat_src = (field_level_counts(df).reset_index()
                .melt(id_vars="job_family_group", var_name="level", value_name="postings"))
    st.altair_chart(
        alt.Chart(heat_src).mark_rect().encode(
            x=alt.X("level:N", sort=LEVEL_ORDER, title=t("c_level")),
            y=alt.Y("job_family_group:N", title=t("c_field")),
            color=alt.Color("postings:Q", scale=alt.Scale(scheme="teals"), title=t("c_postings")),
            tooltip=[alt.Tooltip("job_family_group", title=t("c_field")),
                     alt.Tooltip("level", title=t("c_level")),
                     alt.Tooltip("postings", title=t("c_postings"))],
        ).properties(title=t("jp_dist_title")),
        use_container_width=True,
    )
    st.caption(t("jp_dist_cap"))
    st.divider()

    st.header(t("jp_h_skill"))
    _frame(st, t, "reader_planner", "jp_q_skill")
    fields = [t("jp_all")] + sorted(df["job_family_group"].unique())
    pick = st.selectbox(t("jp_skill_filter"), fields)
    sub = df if pick == t("jp_all") else df[df["job_family_group"] == pick]
    kw = skill_keyword_counts(sub, SYNTH_TEXT_COLS).rename(columns={"skill": t("c_skill")})
    st.altair_chart(
        _bar(alt, kw, t("c_postings"), t("c_skill"), "")
        .properties(title=t("jp_skill_title"), height=max(180, 26 * len(kw))),
        use_container_width=True,
    )
    st.caption(t("jp_skill_cap"))
    st.divider()

    st.header(t("jp_h_channel"))
    _frame(st, t, "reader_planner", "jp_q_channel")
    ch = top_counts(df["source_platform"], 20, "channel").rename(columns={"channel": t("c_channel")})
    st.altair_chart(
        _bar(alt, ch, t("c_postings"), t("c_channel"), "").properties(title=t("jp_channel_title")),
        use_container_width=True,
    )
    st.caption(t("jp_channel_cap"))
    st.divider()

    st.header(t("jp_h_quality"))
    _frame(st, t, "reader_planner", "jp_q_quality")
    q = synth_quality(df)
    dash = "—"
    rows = [
        (t("jp_m_total"), f"{q['total']:,}", ""),
        (t("jp_m_nfkc"), dash if q["nfkc"] is None else f"{q['nfkc']:,}", t("jp_m_nfkc_help")),
        (t("jp_m_dup"), dash if q["dup"] is None else f"{q['dup']:,}", t("jp_m_dup_help")),
        (t("jp_m_salary_fmt"), dash if q["salary_fmt"] is None else str(q["salary_fmt"]), t("jp_m_salary_help")),
        (t("jp_m_field"), str(q["field_variants"]), t("jp_m_field_help")),
    ]
    st.dataframe(
        pd.DataFrame({t("jp_metric"): [r[0] for r in rows], t("jp_value"): [r[1] for r in rows]}),
        use_container_width=True, hide_index=True,
    )
    for label, _v, help_txt in rows:
        if help_txt:
            st.caption(f"· **{label}** — {help_txt}")
    st.markdown(f"**{t('jp_nulls_title')}**")
    st.dataframe(
        q["nulls"].rename(columns={"column": t("jp_null_col"), "rate": t("jp_null_rate")}),
        use_container_width=True, hide_index=True,
    )
    st.divider()

    st.header(t("jp_h_method"))
    _frame(st, t, "reader_planner", "jp_q_quality")
    st.markdown(t("jp_method_body"))
    _render_notimpl_and_bench(st, t)


# ---------- GLOBAL ATS TRACK ----------

def render_ats(st, alt, t) -> None:
    runs = list_ats_runs()
    if not runs:
        st.error("ATS canonical parquet not found under data/golden-set/public-it-postings-canonical/")
        return
    default = runs.index("2026-08-30-scaleup") if "2026-08-30-scaleup" in runs else len(runs) - 1
    run = st.selectbox(t("ats_partition"), runs, index=default)
    df = load_ats(run)
    st.info(t("ats_note"))

    st.header(t("ats_h_summary"))
    _frame(st, t, "reader_planner", "ats_q_summary")
    st.markdown(_kpi_row([
        (f"{len(df):,}", t("k_ats_records")),
        (f"{df['company_name'].nunique():,}", t("k_ats_companies")),
        (f"{df['source_platform'].nunique()}", t("k_ats_sources")),
    ]), unsafe_allow_html=True)
    st.divider()

    st.header(t("ats_h_company"))
    _frame(st, t, "reader_planner", "ats_q_company")
    comp = top_counts(df["company_name"], 20, "company").rename(columns={"company": t("c_company")})
    st.altair_chart(
        _bar(alt, comp, t("c_postings"), t("c_company"), "")
        .properties(title=t("ats_company_title"), height=max(200, 24 * len(comp))),
        use_container_width=True,
    )
    st.divider()

    st.header(t("ats_h_role"))
    _frame(st, t, "reader_planner", "ats_q_role")
    role = top_counts(df["title"], 20, "title").rename(columns={"title": t("c_title")})
    st.altair_chart(
        _bar(alt, role, t("c_postings"), t("c_title"), "")
        .properties(title=t("ats_role_title"), height=max(200, 24 * len(role))),
        use_container_width=True,
    )
    st.divider()

    st.header(t("ats_h_location"))
    _frame(st, t, "reader_planner", "ats_q_location")
    loc = top_counts(df["location"], 20, "location").rename(columns={"location": t("c_location")})
    st.altair_chart(
        _bar(alt, loc, t("c_postings"), t("c_location"), "")
        .properties(title=t("ats_location_title"), height=max(200, 24 * len(loc))),
        use_container_width=True,
    )
    st.divider()

    st.header(t("ats_h_skill"))
    _frame(st, t, "reader_planner", "ats_q_skill")
    kw = skill_keyword_counts(df, ATS_TEXT_COLS).rename(columns={"skill": t("c_skill")})
    st.altair_chart(
        _bar(alt, kw, t("c_postings"), t("c_skill"), "")
        .properties(title=t("ats_skill_title"), height=max(180, 26 * len(kw))),
        use_container_width=True,
    )
    st.caption(t("ats_skill_cap"))

    csm = company_skill_matrix(df, ATS_TEXT_COLS)
    if not csm.empty:
        st.altair_chart(
            alt.Chart(csm).mark_rect().encode(
                x=alt.X("skill:N", title=t("c_skill")),
                y=alt.Y("company:N", title=t("c_company")),
                color=alt.Color("postings:Q", scale=alt.Scale(scheme="teals"), title=t("c_postings")),
                tooltip=[alt.Tooltip("company", title=t("c_company")),
                         alt.Tooltip("skill", title=t("c_skill")),
                         alt.Tooltip("postings", title=t("c_postings"))],
            ).properties(title=t("ats_company_skill_title")),
            use_container_width=True,
        )
    st.divider()

    st.header(t("ats_h_source"))
    _frame(st, t, "reader_planner", "ats_q_source")
    src = top_counts(df["source_platform"], 10, "source").rename(columns={"source": t("c_source")})
    st.altair_chart(
        _bar(alt, src, t("c_postings"), t("c_source"), "", color="#5b7fa6")
        .properties(title=t("ats_source_title")),
        use_container_width=True,
    )
    st.divider()

    st.header(t("ats_h_method"))
    _frame(st, t, "reader_planner", "ats_q_summary")
    st.markdown(t("ats_method_body"))
    _render_notimpl_and_bench(st, t)


def _render_notimpl_and_bench(st, t) -> None:
    st.subheader(t("notimpl_title"))
    for line in notimpl(_LANG[0]):
        st.markdown(f"- {line}")
    st.subheader(t("bench_title"))
    bt = pd.DataFrame(bench_table(_LANG[0]),
                      columns=[t("bench_c_service"), t("bench_c_took"), t("bench_c_apply")])
    st.dataframe(bt, use_container_width=True, hide_index=True)
    st.caption(t("bench_more"))


_LANG = ["ko"]  # render 함수들이 참조하는 현재 언어 (main 에서 설정)


def main() -> None:
    import altair as alt
    import streamlit as st

    st.set_page_config(page_title="JDF Standardization Report", layout="wide")
    lang = LANGS[st.sidebar.radio("Language / 言語 / 언어", list(LANGS.keys()), index=1)]
    _LANG[0] = lang
    t = make_t(lang)
    st.markdown(_css(), unsafe_allow_html=True)

    st.title(t("app_title"))
    ds_key = st.radio(
        t("pick_dataset"),
        options=list(DATASETS.keys()),
        format_func=lambda k: DATASETS[k][lang],
    )
    st.caption(t("split_note"))
    st.divider()

    if ds_key == "japan":
        render_japan(st, alt, t)
    else:
        render_ats(st, alt, t)


if __name__ == "__main__":
    main()
