"""Prove a negative amount fails the intended dbt test in a disposable warehouse."""

import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

with TemporaryDirectory() as tmp:
    sandbox = Path(tmp)
    project = sandbox / "dbt_project"
    shutil.copytree(
        "dbt_project",
        project,
        ignore=shutil.ignore_patterns("target", "logs", "*.duckdb*"),
    )
    db = sandbox / Path(os.environ["WAREHOUSE_PATH"]).name
    shutil.copyfile(os.environ["WAREHOUSE_PATH"], db)
    env = {**os.environ, "WAREHOUSE_PATH": str(db)}
    orders = project / "seeds/orders.csv"
    with orders.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows[0]["amount_cents"] = "-1"
    with orders.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    subprocess.run(
        ["dbt", "seed", "--select", "orders", "--full-refresh", "--profiles-dir", "."],
        check=True,
        cwd=project,
        env=env,
    )
    check = subprocess.run(
        ["dbt", "test", "--select", "nonnegative_order_amount", "--profiles-dir", "."],
        cwd=project,
        env=env,
    )
    results = json.loads((project / "target/run_results.json").read_text())["results"]
    if (
        check.returncode != 1
        or len(results) != 1
        or results[0]["status"] != "fail"
        or results[0]["failures"] != 1
        or not results[0]["unique_id"].endswith(".nonnegative_order_amount")
    ):
        raise RuntimeError(
            "The data quality gate did not reject exactly the injected row"
        )
