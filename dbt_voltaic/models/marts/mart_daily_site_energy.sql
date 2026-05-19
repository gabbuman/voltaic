-- Daily energy + utilization per site. This is the time-series spine of
-- the Evidence dashboard: one row per (site, day).

with s as (
    select * from {{ ref('mart_session_summary') }}
)

select
    site,
    session_dt,
    count(*)                                          as sessions,
    countif(not is_idle_session)                      as charging_sessions,
    count(distinct station_id)                        as active_stations,
    round(sum(energy_kwh), 2)                          as total_energy_kwh,
    round(avg(energy_kwh), 3)                          as avg_energy_kwh,
    round(sum(duration_hr), 2)                          as total_plugged_in_hr,
    round(avg(duration_min), 1)                         as avg_session_min,
    round(max(peak_power_kw), 2)                        as max_peak_power_kw
from s
group by site, session_dt
order by site, session_dt
