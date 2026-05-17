"""Smoke test: authenticate with the GCP service account and confirm BigQuery is reachable.

Run from project root:
    GOOGLE_APPLICATION_CREDENTIALS=secrets/voltaic-sa.json uv run python scripts/bq_smoke_test.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from google.cloud import bigquery
from google.oauth2 import service_account

KEY_PATH = Path(__file__).resolve().parent.parent / "secrets" / "voltaic-sa.json"


def main() -> int:
    if not KEY_PATH.exists():
        print(f"FAIL: service account key not found at {KEY_PATH}", file=sys.stderr)
        return 1

    with KEY_PATH.open() as f:
        sa_info = json.load(f)
    project_id = sa_info["project_id"]
    sa_email = sa_info["client_email"]

    print(f"Project:        {project_id}")
    print(f"Service acct:   {sa_email}")

    credentials = service_account.Credentials.from_service_account_file(str(KEY_PATH))
    client = bigquery.Client(project=project_id, credentials=credentials)

    datasets = list(client.list_datasets())
    print(f"Datasets found: {len(datasets)}")
    for ds in datasets:
        print(f"  - {ds.dataset_id}")

    query = "SELECT 1 + 1 AS answer"
    result = next(iter(client.query(query).result()))
    print(f"SELECT 1+1 ->   {result.answer}")

    print("\nOK — BigQuery auth wired up.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
