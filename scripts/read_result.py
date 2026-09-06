"""7차시 — 최종 저장 결과(`data/processed/postings_clean.parquet`)를 읽어 요약 출력.

원샷 실행(`scripts/run_pipeline.sh`)의 마지막 "읽기" 단계이자, 서빙 레이어의
가장 단순한 형태(스크립트 출력). 대시보드는 같은 파일을 화면으로 보여준다.

실행: python scripts/read_result.py
"""
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
PARQUET = REPO_ROOT / "data" / "processed" / "postings_clean.parquet"
sys.path.insert(0, str(REPO_ROOT / "app"))

from dashboard import SYNTH_TEXT_COLS, skill_keyword_counts, top_counts  # noqa: E402


def main() -> None:
    if not PARQUET.exists():
        sys.exit(f"저장 결과 없음: {PARQUET} — 파이프라인을 먼저 실행하세요.")

    df = pd.read_parquet(PARQUET)
    if "is_negative_control" in df.columns:
        df = df[~df["is_negative_control"].fillna(False).astype(bool)]

    print(f"파일         : {PARQUET.relative_to(REPO_ROOT)}")
    print(f"공고 수      : {len(df):,}")
    print(f"채널 수      : {df['source_platform'].nunique()}")
    print(f"직무 분야 수 : {df['job_family_group'].nunique()}")
    print(f"posting_id 중복: {int(df['posting_id'].duplicated().sum())}")

    print("\n채널별 공고 수")
    for _, r in top_counts(df["source_platform"], 10, "channel").iterrows():
        print(f"  {r['channel']:<16} {r['postings']}")

    print("\n스킬 키워드 상위 5 (표기 변형 합산)")
    for _, r in skill_keyword_counts(df, SYNTH_TEXT_COLS).head(5).iterrows():
        print(f"  {r['skill']:<24} {r['postings']}")


if __name__ == "__main__":
    main()
