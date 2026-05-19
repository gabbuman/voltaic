"""Load DuckDB silver Parquet into BigQuery `voltaic_raw`.

This is the silver→warehouse handoff (ADR-0008 supersedes ADR-0002's
`bq load` of Spark output; the contract — typed Parquet into voltaic_raw
— is unchanged, only the producing engine changed).

Parquet carries its own schema, so BigQuery infers types directly; no
schema file to drift. WRITE_TRUNCATE keeps the load idempotent, which
matters for the weekly CI rebuild (sandbox 60-day table expiry).

Run from project root:
    uv run python scripts/load_silver_to_bq.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from google.cloud import bigquery
from google.oauth2 import service_account

REPO_ROOT = Path(__file__).resolve().parent.parent
KEY_PATH = REPO_ROOT / "secrets" / "voltaic-sa.json"
SILVER_ROOT = REPO_ROOT / "data" / "silver"
DATASET = "voltaic_raw"

# silver Parquet file -> BigQuery table name
TABLES = {
    "charging_meter_readings": SILVER_ROOT / "charging_meter_readings.parquet",
    "charging_sessions": SILVER_ROOT / "charging_sessions.parquet",
}


def main() -> int:
    if not KEY_PATH.exists():
        print(f"FAIL: service account key not found at {KEY_PATH}", file=sys.stderr)
        return 1

    with KEY_PATH.open() as f:
        project_id = json.load(f)["project_id"]

    credentials = service_account.Credentials.from_service_account_file(str(KEY_PATH))
    client = bigquery.Client(project=project_id, credentials=credentials)

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    for table_name, parquet_path in TABLES.items():
        if not parquet_path.exists():
            print(f"FAIL: missing {parquet_path} — run transform.acn_silver first",
                  file=sys.stderr)
            return 1

        table_id = f"{project_id}.{DATASET}.{table_name}"
        with parquet_path.open("rb") as src:
            job = client.load_table_from_file(src, table_id, job_config=job_config)
        job.result()  # block until done; raises on failure

        table = client.get_table(table_id)
        print(f"OK  {table_id:55s}  {table.num_rows:,} rows, "
              f"{len(table.schema)} cols")

    print("\nSilver landed in BigQuery.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
