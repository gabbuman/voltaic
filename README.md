# Voltaic

> Prosumer analytics lakehouse — EV charging telemetry + solar inverter performance, processed through a PySpark medallion into BigQuery, modeled with dbt, and published to GitHub Pages via Evidence.dev.

**Status:** in active development. See [`PLAN.md`](./PLAN.md) for the full design and weekend-by-weekend roadmap.

## Stack

| Layer        | Tool                                   |
|--------------|----------------------------------------|
| Ingestion    | Python + PySpark (bronze / silver)     |
| Warehouse    | BigQuery (sandbox)                     |
| Modeling     | dbt Core (gold marts + tests + docs)   |
| BI           | Evidence.dev (static site)             |
| Orchestration| GitHub Actions (cron)                  |
| Packaging    | uv                                     |

## Data sources

- **Caltech ACN-Data** — EV charging sessions from Caltech, JPL, and an office site.
- **NREL PVDAQ** — solar inverter time-series (parquet on AWS Open Data, `s3://oedi-data-lake/pvdaq/`).
- **CAISO OASIS** — hourly grid LMPs for the prosumer cost-offset model.

## Local setup

```bash
uv sync                                  # install pinned deps into .venv
cp .env.example .env                     # then fill in values (see below)
mkdir -p secrets                         # gitignored
# drop your GCP service account key at secrets/voltaic-sa.json
uv run python scripts/bq_smoke_test.py   # confirms BigQuery auth works
```

## License

MIT (to be added).
