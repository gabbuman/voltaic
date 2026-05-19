---
title: Voltaic — EV Charging Analytics
---

<div style="float:right; max-width:300px; margin:0 0 1rem 1rem; padding:0.75rem 1rem; border:1px solid var(--grey-300); border-radius:8px; font-size:0.75rem; line-height:1.4; color:var(--grey-600);">

**MVP scope**

Site **office_01** only. Pipeline: ACN-Data → bronze + silver (DuckDB) → BigQuery → dbt gold → Evidence.

_Next: JPL / Caltech sites, NREL solar + CAISO grid joins, CI rebuild & Pages deploy._

</div>

Charging-session analytics for the Caltech ACN research network. Every number
below is computed by the dbt gold marts in BigQuery — no hand-maintained data.

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
