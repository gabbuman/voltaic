"""Silver transform: conform ACN-Data bronze into typed, modeled tables.

Engine: DuckDB. See docs/decisions/0008-duckdb-for-silver-supersedes-spark.md.

Bronze→silver contract:
    * Cast every column from raw VARCHAR to its real type. Bronze landed
      bytes faithfully; silver is where types become trustworthy.
    * Build the composite session key. Bronze's `session_id` is the
      charger/station id (shared across sessions); a session is unique
      only as (site, station, session_start_ts).
    * Emit two grains:
        charging_meter_readings  — one row per meter reading (typed)
        charging_sessions        — one row per session (aggregates)

The transform is intentionally engine-agnostic SQL: promoting silver to
Spark later (ADR-0008) is a swap of executor, not a rewrite of logic.

Run:
    uv run python -m transform.acn_silver
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parent.parent
BRONZE_GLOB = (
    REPO_ROOT / "data" / "bronze" / "charging_meter_readings" / "**" / "*.parquet"
).as_posix()
SILVER_ROOT = REPO_ROOT / "data" / "silver"

# session_start_ts is provenance like 2019-03-25T16:24:42.408146 ; the
# reading timestamp carries an explicit UTC offset (…+00:00).
READING_TS_FMT = "%Y-%m-%dT%H:%M:%S%z"
SESSION_TS_FMT = "%Y-%m-%dT%H:%M:%S.%f"

# Reading-grain: one typed row per meter sample. session_uid makes a
# session addressable even though session_id alone is the station.
READINGS_SQL = f"""
SELECT
    concat_ws(':', site, session_id, session_start_ts)        AS session_uid,
    site,
    session_id                                                AS station_id,
    strptime(session_start_ts, '{SESSION_TS_FMT}')            AS session_start_ts,
    strptime(reading_ts_raw,   '{READING_TS_FMT}')            AS reading_ts,
    session_dt,
    TRY_CAST("Charging Current (A)"  AS DOUBLE)               AS charging_current_a,
    TRY_CAST("Actual Pilot (A)"      AS DOUBLE)               AS actual_pilot_a,
    TRY_CAST("Voltage (V)"           AS DOUBLE)               AS voltage_v,
    "Charging State"                                          AS charging_state,
    TRY_CAST("Energy Delivered (kWh)" AS DOUBLE)              AS energy_delivered_kwh,
    TRY_CAST("Power (kW)"            AS DOUBLE)                AS power_kw
FROM read_parquet('{BRONZE_GLOB}')
"""

# Session-grain: collapse readings to one row per session. Energy is a
# cumulative counter within a session, so the session total is its max.
SESSIONS_SQL = """
SELECT
    session_uid,
    any_value(site)             AS site,
    any_value(station_id)       AS station_id,
    any_value(session_start_ts) AS session_start_ts,
    any_value(session_dt)       AS session_dt,
    max(reading_ts)             AS session_end_ts,
    date_diff('second', min(reading_ts), max(reading_ts)) / 60.0
                                AS duration_min,
    count(*)                    AS n_readings,
    max(energy_delivered_kwh)   AS energy_delivered_kwh,
    max(power_kw)               AS peak_power_kw,
    avg(power_kw)               AS avg_power_kw,
    max(charging_current_a)     AS peak_current_a
FROM silver_readings
GROUP BY session_uid
"""


def build_silver(con: duckdb.DuckDBPyConnection) -> tuple[int, int]:
    SILVER_ROOT.mkdir(parents=True, exist_ok=True)

    con.execute(f"CREATE TEMP VIEW silver_readings AS {READINGS_SQL}")
    con.execute(f"CREATE TEMP VIEW silver_sessions AS {SESSIONS_SQL}")

    readings_out = (SILVER_ROOT / "charging_meter_readings.parquet").as_posix()
    sessions_out = (SILVER_ROOT / "charging_sessions.parquet").as_posix()

    con.execute(
        f"COPY (SELECT * FROM silver_readings) TO '{readings_out}' (FORMAT PARQUET)"
    )
    con.execute(
        f"COPY (SELECT * FROM silver_sessions) TO '{sessions_out}' (FORMAT PARQUET)"
    )

    n_readings = con.execute(
        f"SELECT count(*) FROM read_parquet('{readings_out}')"
    ).fetchone()[0]
    n_sessions = con.execute(
        f"SELECT count(*) FROM read_parquet('{sessions_out}')"
    ).fetchone()[0]

    # Cheap contract checks — fail loud if the cast or key logic broke.
    bad_ts = con.execute(
        f"SELECT count(*) FROM read_parquet('{readings_out}') "
        f"WHERE reading_ts IS NULL OR session_start_ts IS NULL"
    ).fetchone()[0]
    if bad_ts:
        raise SystemExit(f"FAIL: {bad_ts:,} rows with unparseable timestamps")

    print(f"OK — silver_readings: {n_readings:,} rows -> {readings_out}")
    print(f"OK — silver_sessions: {n_sessions:,} rows -> {sessions_out}")
    return n_readings, n_sessions


def main() -> int:
    con = duckdb.connect()
    try:
        build_silver(con)
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
