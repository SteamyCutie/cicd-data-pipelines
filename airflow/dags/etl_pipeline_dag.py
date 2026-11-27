"""Publish a daily, fully tested rebuild on one host with a shared warehouse directory."""

import hashlib
import os
from datetime import timedelta
from pathlib import Path
import subprocess

import duckdb
import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator


def candidate_path(run_id):
    root = Path(os.getenv("RETAIL_DATA_DIR", "/tmp/retail")).resolve()
    root.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(run_id.encode()).hexdigest()
    return str(root / f"{key}.duckdb")


def build_candidate(path):
    project = Path(__file__).resolve().parents[2] / "dbt_project"
    env = {**os.environ, "WAREHOUSE_PATH": path, "DBT_SCHEMA": "analytics"}
    subprocess.run(
        [os.getenv("DBT_BIN", "dbt"), "build", "--profiles-dir", ".", "--target", "ci"],
        cwd=project,
        env=env,
        check=True,
    )
    return path


def publish_candidate(path):
    candidate = Path(path)
    live = candidate.with_name("retail.duckdb")
    # Copy using DuckDB's checkpointed single file, then atomically promote.
    # Keep the run-scoped candidate until publication so a failed retry can resume.
    import shutil

    with duckdb.connect(path, read_only=True) as db:
        count, cents = db.execute(
            "select sum(orders_placed), sum(revenue_cents) from analytics.fct_daily_revenue"
        ).fetchone()
        if not count or cents is None or cents < 0:
            raise ValueError("Revenue mart failed publication checks")
    pending = candidate.with_suffix(".publishing")
    shutil.copyfile(candidate, pending)
    os.replace(pending, live)
    return {"orders": int(count), "revenue_cents": int(cents)}


with DAG(
    "retail_revenue",
    description="Rebuild retail revenue and atomically publish the tested DuckDB warehouse.",
    schedule="@daily",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    dagrun_timeout=timedelta(minutes=30),
    default_args={
        "owner": "analytics",
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
    },
    tags=["retail", "dbt"],
) as dag:
    prepare = PythonOperator(task_id="prepare", python_callable=candidate_path)
    build = PythonOperator(
        task_id="build_and_test",
        python_callable=build_candidate,
        op_kwargs={"path": prepare.output},
    )
    publish = PythonOperator(
        task_id="publish",
        python_callable=publish_candidate,
        op_kwargs={"path": build.output},
    )
