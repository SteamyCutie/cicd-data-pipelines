from pathlib import Path
import subprocess
from unittest.mock import patch

import duckdb
import pendulum
import pytest
from airflow.models import DagBag

DAGS = Path(__file__).resolve().parents[1] / "dags"


@pytest.fixture(scope="module")
def dag():
    bag = DagBag(dag_folder=str(DAGS), include_examples=False)
    assert not bag.import_errors, bag.import_errors
    return bag.dags["retail_revenue"]


def test_contract(dag):
    assert dag.schedule_interval == "@daily" and not dag.catchup
    assert dag.max_active_runs == 1 and dag.tags
    assert dag.get_task("prepare").downstream_task_ids == {"build_and_test"}
    assert dag.get_task("build_and_test").downstream_task_ids == {"publish"}
    assert all(t.owner == "analytics" and t.retries >= 1 for t in dag.tasks)


def test_failed_build_propagates(dag, tmp_path):
    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "dbt")):
        with pytest.raises(subprocess.CalledProcessError):
            dag.get_task("build_and_test").python_callable(str(tmp_path / "candidate.duckdb"))


def test_publish_rejects_bad_candidate(dag, tmp_path):
    live = tmp_path / "retail.duckdb"
    live.write_bytes(b"previous warehouse")
    with pytest.raises(duckdb.Error):
        dag.get_task("publish").python_callable(str(tmp_path / "absent.duckdb"))
    assert live.read_bytes() == b"previous warehouse"


def test_full_dag(dag, tmp_path, monkeypatch):
    monkeypatch.setenv("RETAIL_DATA_DIR", str(tmp_path))
    result = dag.test(execution_date=pendulum.datetime(2025, 6, 4, tz="UTC"))
    assert result.state == "success"
    with duckdb.connect(str(tmp_path / "retail.duckdb"), read_only=True) as db:
        assert db.execute("select sum(orders_placed), sum(revenue_cents) from analytics.fct_daily_revenue").fetchone() == (5, 7000)
