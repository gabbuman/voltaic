select
    site,
    session_dt,
    sessions,
    charging_sessions,
    active_stations,
    total_energy_kwh,
    avg_energy_kwh,
    total_plugged_in_hr,
    avg_session_min,
    max_peak_power_kw
from solardataset-496600.voltaic_gold.mart_daily_site_energy
order by session_dt
