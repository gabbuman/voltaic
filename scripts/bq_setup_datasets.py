"""Provision BigQuery datasets for Voltaic. Idempotent — safe to re-run.

Datasets:
    voltaic_raw   — landings from DuckDB silver (Parquet load target)
    voltaic_gold  — dbt mart outputs (facts, dims)
    voltaic_ci    — scratch space for CI runs (PR builds land here, never touch real data)

All datasets:
    * location = US (BigQuery sandbox default, free-tier eligible)
    * default_table_expiration_ms = 60 days (matches sandbox forced expiry, makes it explicit)

Run from project root:
    uv run python scripts/bq_setup_datasets.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from google.cloud import bigquery
from google.oauth2 import service_account

KEY_PATH = Path(__file__).resolve().parent.parent / "secrets" / "voltaic-sa.json"
LOCATION = "US"
SIXTY_DAYS_MS = 60 * 24 * 60 * 60 * 1000

DATASETS = {
    "voltaic_raw": "Raw landings from DuckDB silver (Parquet load target)",
    "voltaic_gold": "dbt gold marts — facts, dimensions, snapshots",
    "voltaic_ci": "Scratch space for CI runs; PR builds land here",
}


def main() -> int:
    if not KEY_PATH.exists():
        print(f"FAIL: service account key not found at {KEY_PATH}", file=sys.stderr)
        return 1

    with KEY_PATH.open() as f:
        project_id = json.load(f)["project_id"]

    credentials = service_account.Credentials.from_service_account_file(str(KEY_PATH))
    client = bigquery.Client(project=project_id, credentials=credentials)

    for dataset_id, description in DATASETS.items():
        full_id = f"{project_id}.{dataset_id}"
        dataset = bigquery.Dataset(full_id)
        dataset.location = LOCATION
        dataset.description = description
        dataset.default_table_expiration_ms = SIXTY_DAYS_MS

        created = client.create_dataset(dataset, exists_ok=True)
        # exists_ok=True won't update existing settings, so patch defensively
        created.description = description
        created.default_table_expiration_ms = SIXTY_DAYS_MS
        client.update_dataset(created, ["description", "default_table_expiration_ms"])

        print(f"OK  {full_id:50s}  {description}")

    print("\nAll datasets ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
