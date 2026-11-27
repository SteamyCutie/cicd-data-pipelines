"""Summarize dbt statuses even when compilation fails before results exist."""
import json
from collections import Counter
from pathlib import Path

results = Path("dbt_project/target/run_results.json")
print("### dbt build")
if results.exists():
    counts = Counter(row["status"] for row in json.loads(results.read_text())["results"])
    for status, count in sorted(counts.items()):
        print(f"- {status}: {count}")
else:
    print("No results file was produced. Inspect the preceding step log.")
