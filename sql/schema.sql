DROP TABLE IF EXISTS experiment_events;

CREATE TABLE experiment_events (
    user_id TEXT PRIMARY KEY,
    experiment_group TEXT NOT NULL,
    device_type TEXT NOT NULL,
    traffic_source TEXT NOT NULL,
    region TEXT NOT NULL,
    landing_page TEXT NOT NULL,
    sessions INTEGER NOT NULL,
    avg_session_duration_sec REAL NOT NULL,
    pages_viewed REAL NOT NULL,
    signed_up INTEGER NOT NULL,
    purchased INTEGER NOT NULL,
    order_value REAL NOT NULL,
    revenue REAL NOT NULL
);
