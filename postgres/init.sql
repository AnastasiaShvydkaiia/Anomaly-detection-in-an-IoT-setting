CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    station_id TEXT,
    timestamp TIMESTAMP,
    temperature FLOAT,
    humidity FLOAT,
    sound_volume FLOAT,
    anomaly_score FLOAT,
    is_anomaly BOOLEAN
);
