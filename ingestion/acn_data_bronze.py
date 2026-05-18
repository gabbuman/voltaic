"""Bronze ingestion: ACN-Data per-session meter readings.

Reads the static-mirror CSV.gz files for a given site, adds provenance
metadata parsed from the filename (session_id, session_start_ts), and
writes them as Parquet partitioned by site + session_dt.

Engine: DuckDB. See docs/decisions/0007-duckdb-for-bronze-not-pyspark.md
for why bronze runs on DuckDB while silver stays on PySpark (ADR-0002).

Bronze layer contract:
    * Land raw bytes faithfully — every source column stays VARCHAR,
      no type coercion, no business logic. Silver casts.
    * Add only provenance columns the source data doesn't already carry.
    * Partitioning here is for read efficiency, not schema enforcement.

Run:
    uv run python -m ingestion.acn_data_bronze --site office_01
    uv run python -m ingestion.acn_data_bronze --site caltech --sample 500
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = REPO_ROOT.parent / "voltaic-data" / "acn-data-static" / "time series data"
BRONZE_ROOT = REPO_ROOT / "data" / "bronze" / "charging_meter_readings"

# Filename: 19-102-260-1633-2019-03-25T16-24-42-408146.csv.gz
#   session_id = 19-102-260-1633
#   ts portion = 2019-03-25T16-24-42-408146  (hyphens where ISO uses : and .)
# DuckDB regexp groups: \1 = session_id, \2 = date, \3 h, \4 m, \5 s, \6 micro
FILENAME_RE = (
    r"([\w-]+?)-"                       # session_id (lazy)
    r"(\d{4}-\d{2}-\d{2})T"             # date
    r"(\d{2})-(\d{2})-(\d{2})-(\d+)"    # H-M-S-micro
    r"\.csv\.gz$"
)


def ingest_site(con: duckdb.DuckDBPyConnection, site: str, sample: int | None) -> int:
    """Ingest one site folder. Returns row count written."""
    site_dir = SOURCE_ROOT / site
    if not site_dir.exists():
        raise SystemExit(f"FAIL: source dir not found: {site_dir}")

    # Recursive glob — DuckDB handles `**` natively (the thing Spark
    # tripped on under Windows). Forward slashes are fine on Windows too.
    glob = (site_dir.as_posix() + "/**/*.csv.gz")
    # DuckDB's COPY won't mkdir the parent chain — create it ourselves.
    BRONZE_ROOT.mkdir(parents=True, exist_ok=True)
    out_path = BRONZE_ROOT.as_posix()

    limit_sql = f"LIMIT {int(sample)}" if sample is not None else ""

    # all_varchar: bronze lands bytes faithfully; no type inference.
    # filename: carries provenance so we can parse session_id / start ts.
    # The source's first column has an empty header (the reading timestamp);
    # read_csv names it "column0" — we rename it to reading_ts_raw.
    con.execute(
        f"""
        COPY (
            SELECT
                * EXCLUDE (filename, column0),
                column0                                   AS reading_ts_raw,
                regexp_extract(filename, '{FILENAME_RE}', 1) AS session_id,
                concat(
                    regexp_extract(filename, '{FILENAME_RE}', 2), 'T',
                    regexp_extract(filename, '{FILENAME_RE}', 3), ':',
                    regexp_extract(filename, '{FILENAME_RE}', 4), ':',
                    regexp_extract(filename, '{FILENAME_RE}', 5), '.',
                    regexp_extract(filename, '{FILENAME_RE}', 6)
                )                                         AS session_start_ts,
                '{site}'                                  AS site,
                CAST(
                    strptime(
                        regexp_extract(filename, '{FILENAME_RE}', 2),
                        '%Y-%m-%d'
                    ) AS DATE
                )                                         AS session_dt
            FROM read_csv(
                '{glob}',
                header = true,
                all_varchar = true,
                filename = true
            )
            {limit_sql}
        )
        TO '{out_path}'
        (FORMAT PARQUET, PARTITION_BY (site, session_dt), OVERWRITE_OR_IGNORE);
        """
    )

    n = con.execute(
        f"SELECT count(*) FROM read_parquet('{out_path}/**/*.parquet') "
        f"WHERE site = '{site}'"
    ).fetchone()[0]
    print(f"OK — wrote {n:,} rows for site={site} to {out_path}")
    return n


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--site", required=True, choices=["office_01", "jpl", "caltech"])
    p.add_argument("--sample", type=int, default=None,
                   help="Limit rows for quick smoke testing")
    args = p.parse_args()

    con = duckdb.connect()
    try:
        ingest_site(con, site=args.site, sample=args.sample)
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
