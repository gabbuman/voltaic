---
title: Voltaic — EV Charging Analytics
---

<div style="float:right; max-width:300px; margin:0 0 1rem 1rem; padding:0.75rem 1rem; border:1px solid var(--grey-300); border-radius:8px; font-size:0.75rem; line-height:1.4; color:var(--grey-600);">

**MVP scope**

Site **office_01** only, one end-to-end vertical slice.

_Next: JPL / Caltech sites, NREL solar + CAISO grid joins, scheduled CI data rebuild._

</div>

**Voltaic** is a portfolio data-engineering project: a small analytics lakehouse
that turns raw electric-vehicle charging logs into a live dashboard.

**The data** is the [Caltech ACN-Data](https://ev.caltech.edu/dataset) research
dataset — real EV charging sessions from an instrumented workplace car park
("office_01"). Each session is thousands of per-second meter readings: current,
voltage, power, and cumulative energy delivered.

**What you're looking at**, top to bottom: headline totals across the whole
period; energy delivered and session counts per day; how load is distributed
across the eight charging stations; and a drill-down of individual sessions.
Every number is computed by SQL models in BigQuery and refreshed by the
pipeline below — nothing here is hand-entered.

```sql kpis
select
    sum(total_energy_kwh)              as total_kwh,
    sum(sessions)                      as total_sessions,
    sum(charging_sessions)             as charging_sessions,
    max(active_stations)               as stations,
    round(avg(avg_session_min), 0)     as avg_session_min
from voltaic_gold.daily_energy
```

<BigValue data={kpis} value=total_kwh fmt='#,##0 "kWh"' title="Energy Delivered"/>
<BigValue data={kpis} value=total_sessions fmt='#,##0' title="Sessions"/>
<BigValue data={kpis} value=charging_sessions fmt='#,##0' title="Active Charges"/>
<BigValue data={kpis} value=stations title="Stations"/>
<BigValue data={kpis} value=avg_session_min fmt='#,##0 "min"' title="Avg Plug-in"/>

## Energy delivered over time

```sql daily
select
    session_dt,
    total_energy_kwh,
    sessions,
    charging_sessions
from voltaic_gold.daily_energy
order by session_dt
```

<LineChart
    data={daily}
    x=session_dt
    y=total_energy_kwh
    title="Daily Energy Delivered (kWh) — office_01"
    yAxisTitle="kWh"
/>

<BarChart
    data={daily}
    x=session_dt
    y=sessions
    title="Sessions per Day"
/>

## Throughput by station

```sql by_station
select
    station_id,
    count(*)                              as sessions,
    round(sum(energy_kwh), 1)             as energy_kwh,
    round(avg(duration_min), 0)           as avg_min
from voltaic_gold.session_summary
group by station_id
order by energy_kwh desc
```

<BarChart
    data={by_station}
    x=station_id
    y=energy_kwh
    swapXY=true
    title="Total Energy by Charging Station (kWh)"
/>

## Session detail

```sql recent
select
    session_start_ts,
    station_id,
    duration_min,
    energy_kwh,
    peak_power_kw,
    is_idle_session
from voltaic_gold.session_summary
order by session_start_ts desc
limit 25
```

<DataTable data={recent} rows=10>
    <Column id=session_start_ts title="Start"/>
    <Column id=station_id title="Station"/>
    <Column id=duration_min title="Duration (min)" fmt='#,##0'/>
    <Column id=energy_kwh title="Energy (kWh)" fmt='#,##0.00'/>
    <Column id=peak_power_kw title="Peak kW" fmt='#,##0.0'/>
    <Column id=is_idle_session title="Idle?"/>
</DataTable>

---

## How this is built

A medallion lakehouse. Raw files in, trustworthy marts out, a static site on top.

```
Caltech ACN-Data (.csv.gz, ~1,474 session files)
        │
        ▼  bronze — DuckDB: land raw bytes faithfully, add provenance
   data/bronze/*.parquet
        │
        ▼  silver — DuckDB: cast types, build composite session key
   charging_meter_readings (7.6M rows) · charging_sessions (1,474)
        │
        ▼  load — Parquet → BigQuery (voltaic_raw), idempotent
   BigQuery
        │
        ▼  gold — dbt Core: tested SQL marts (session + daily grain)
   voltaic_gold.mart_session_summary · mart_daily_site_energy
        │
        ▼  present — Evidence.dev queries gold, renders this page
   static site
```

DuckDB does bronze and silver because at this data size a single-node engine
is the honest choice; the transform layer is kept engine-agnostic so it can be
promoted to Spark if the volume ever justifies it. Design decisions are
recorded as ADRs in the repo's `docs/decisions/` log.

## How this site deploys

Every push to `main` that touches the site runs a **GitHub Actions** workflow
(`.github/workflows/deploy.yml`):

1. **Inject the warehouse credential.** The Google service-account key is a
   GitHub repo secret (`GCP_SA_KEY`) — never in git. A step reconstructs the
   gitignored connection file from it, on the runner only.
2. **Generate data from BigQuery.** `evidence sources --strict` queries the
   gold marts and materialises them as static query files. `--strict` fails
   the build on any warehouse error, so a data-less site can never ship.
3. **Build & verify.** `evidence build` renders the static site; a guard
   asserts the data manifest exists before going further.
4. **Publish.** The build is uploaded as a Pages artifact and served via
   `deploy-pages` — no `gh-pages` branch, no generated files committed.

The whole chain is reproducible from a clean clone: the only thing not in the
repo is the secret. _(See ADR-0009 for why the artifact API over a branch, and
how the secret is scoped.)_
