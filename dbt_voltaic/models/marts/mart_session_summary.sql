-- One curated row per charging session: the session-grain mart Evidence
-- and ad-hoc analysis read. Silver already aggregated to session grain;
-- this mart adds business-facing derived fields and light QA filtering.

with sessions as (
    select * from {{ source('raw', 'charging_sessions') }}
)

select
    session_uid,
    site,
    station_id,
    session_start_ts,
    session_end_ts,
    session_dt,
    n_readings,
    round(duration_min, 1)                       as duration_min,
    round(duration_min / 60.0, 2)                as duration_hr,
    round(energy_delivered_kwh, 3)               as energy_kwh,
    round(peak_power_kw, 2)                      as peak_power_kw,
    round(avg_power_kw, 2)                       as avg_power_kw,
    round(peak_current_a, 1)                     as peak_current_a,
    -- A session that delivered no measurable energy is an idle/aborted
    -- plug-in, not a charge. Flag it rather than dropping it.
    coalesce(energy_delivered_kwh, 0) <= 0.01    as is_idle_session
from sessions
