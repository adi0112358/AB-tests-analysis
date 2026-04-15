-- Overall experiment KPI summary
SELECT
    experiment_group,
    COUNT(*) AS users,
    ROUND(100.0 * AVG(signed_up), 2) AS signup_rate_pct,
    ROUND(100.0 * AVG(purchased), 2) AS purchase_rate_pct,
    ROUND(AVG(revenue), 2) AS revenue_per_user,
    ROUND(AVG(avg_session_duration_sec), 2) AS avg_session_duration_sec
FROM experiment_events
GROUP BY experiment_group;

-- Performance by device
SELECT
    device_type,
    experiment_group,
    COUNT(*) AS users,
    ROUND(100.0 * AVG(purchased), 2) AS purchase_rate_pct,
    ROUND(AVG(revenue), 2) AS revenue_per_user
FROM experiment_events
GROUP BY device_type, experiment_group
ORDER BY device_type, experiment_group;

-- Performance by traffic source
SELECT
    traffic_source,
    experiment_group,
    COUNT(*) AS users,
    ROUND(100.0 * AVG(purchased), 2) AS purchase_rate_pct,
    ROUND(AVG(revenue), 2) AS revenue_per_user
FROM experiment_events
GROUP BY traffic_source, experiment_group
ORDER BY traffic_source, experiment_group;
