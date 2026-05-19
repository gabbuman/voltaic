select
    session_uid,
    site,
    station_id,
    session_start_ts,
    session_dt,
    duration_min,
    duration_hr,
    energy_kwh,
    peak_power_kw,
    avg_power_kw,
    is_idle_session
from solardataset-496600.voltaic_gold.mart_session_summary
