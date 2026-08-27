"""4차시 과제 — ATS 공고 수집기 + Spark 정규화를 Airflow로 오케스트레이션.

companies/limit/catalog_url을 DAG params로 노출해 코드 수정 없이 재실행 가능.
매일 실행(@daily)해 "공고는 계속 발생한다"를 주기적 폴링으로 반영한다.
"""
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from airflow.sdk import Param, dag, task


@dag(
    dag_id="collect_public_postings",
    schedule="@daily",
    start_date=datetime(2026, 8, 24),
    catchup=False,
    params={
        "companies": Param(300, type="integer", minimum=1, description="스캔할 회사 수"),
        "limit": Param(None, type=["null", "integer"], description="수집 건수 상한(선택)"),
        "catalog_url": Param(
            "https://raw.githubusercontent.com/ConorsCode/open-jobs-data/main/companies.json",
            type="string",
            description="ATS 보드 카탈로그 URL",
        ),
    },
)
def collect_public_postings():
    @task
    def collect(**context) -> str:
        from ingestion import collect_public_ats_postings as collector

        params = context["params"]
        run_date = context["ds"]
        argv = [
            "--run-date", run_date,
            "--companies", str(params["companies"]),
            "--catalog-url", params["catalog_url"],
        ]
        if params.get("limit"):
            argv += ["--limit", str(params["limit"])]
        collector.main(argv)
        return run_date

    @task
    def normalize(run_date: str) -> None:
        from ingestion import spark_normalize_public_postings as normalizer

        normalizer.main(["--run-date", run_date])

    normalize(collect())


collect_public_postings()
