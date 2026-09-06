"""4차시~7차시 — ATS 공고 수집 + Spark 정규화 오케스트레이션 (+ 선택적 클라우드 적재).

companies/limit/catalog_url을 DAG params로 노출해 코드 수정 없이 재실행 가능.
매일 실행(@daily)해 "공고는 계속 발생한다"를 주기적 폴링으로 반영한다.

push_to_cloud=True 일 때만 normalize 뒤에 GCS 업로드 → BQ MERGE → dbt build 를 돈다
(로컬 실행 경로는 그대로 보존). 실패 시 on_failure_callback 이 알림 JSON을 남긴다.

주의: 클라우드 태스크는 아직 실제 실행/검증되지 않았다 (7차시 "작성만"). ATS 트랙 스키마와
synth 트랙 canonical(jdf.postings_canonical) 스키마 통합은 미검증 — 발표 "아직 보장 못하는 것".
"""
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from airflow.sdk import Param, dag, task

ALERT_DIR = REPO_ROOT / "docs" / "airflow-run-logs" / "alerts"


def write_alert(context) -> None:
    """태스크 실패 시 docs/airflow-run-logs/alerts/<run_id>.json 기록."""
    ALERT_DIR.mkdir(parents=True, exist_ok=True)
    ti = context.get("task_instance")
    run_id = getattr(context.get("dag_run"), "run_id", "unknown")
    payload = {
        "dag_id": getattr(ti, "dag_id", "collect_public_postings"),
        "task_id": getattr(ti, "task_id", None),
        "run_id": run_id,
        "logical_date": str(context.get("logical_date") or context.get("ds")),
        "exception": str(context.get("exception")),
        "recorded_at": datetime.utcnow().isoformat() + "Z",
    }
    out = ALERT_DIR / f"{run_id}.json".replace("/", "_").replace(":", "-")
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))


@dag(
    dag_id="collect_public_postings",
    schedule="@daily",
    start_date=datetime(2026, 8, 24),
    catchup=False,
    default_args={"on_failure_callback": write_alert},
    params={
        "companies": Param(300, type="integer", minimum=1, description="스캔할 회사 수"),
        "limit": Param(None, type=["null", "integer"], description="수집 건수 상한(선택)"),
        "catalog_url": Param(
            "https://raw.githubusercontent.com/ConorsCode/open-jobs-data/main/companies.json",
            type="string",
            description="ATS 보드 카탈로그 URL",
        ),
        "push_to_cloud": Param(
            False, type="boolean",
            description="True면 normalize 뒤 GCS 업로드 → BQ MERGE → dbt build 실행",
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
    def normalize(run_date: str) -> str:
        from ingestion import spark_normalize_public_postings as normalizer

        normalizer.main(["--run-date", run_date])
        return run_date

    @task.branch
    def gate(run_date: str, **context) -> str:
        return "upload_gcs" if context["params"].get("push_to_cloud") else "skip_cloud"

    @task
    def skip_cloud() -> None:
        pass

    @task
    def upload_gcs(run_date: str) -> str:
        import runpy  # cloud/ 스크립트를 argv로 호출 (main() 시그니처 노출 안 함)

        src = f"data/golden-set/public-it-postings-canonical/dt={run_date}"
        sys.argv = ["upload_to_gcs.py", "--run-date", run_date, "--src", src]
        runpy.run_module("cloud.upload_to_gcs", run_name="__main__")
        return run_date

    @task
    def load_bq(run_date: str) -> None:
        import runpy

        sys.argv = ["load_to_bq.py", "--run-date", run_date]
        runpy.run_module("cloud.load_to_bq", run_name="__main__")

    @task.bash
    def dbt_build() -> str:
        return (
            f"cd {REPO_ROOT / 'dbt'} && "
            f"dbt run --profiles-dir . && dbt test --profiles-dir ."
        )

    rd = normalize(collect())
    g = gate(rd)
    up = upload_gcs(rd)
    g >> [up, skip_cloud()]
    up >> load_bq(rd) >> dbt_build()


collect_public_postings()
