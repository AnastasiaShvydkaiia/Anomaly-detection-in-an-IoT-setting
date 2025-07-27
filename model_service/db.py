from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:mypassword@postgres:5432/mydb")
engine = create_engine(DATABASE_URL)

def save_prediction(station_id, timestamp, temp, humidity, sound, score, is_anomaly):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO predictions (
                station_id, timestamp, temperature, humidity,
                sound_volume, anomaly_score, is_anomaly
            )
            VALUES (
                :station_id, :timestamp, :temp, :humidity,
                :sound, :score, :is_anomaly
            );
        """), {
            "station_id": station_id,
            "timestamp": timestamp,
            "temp": float(temp),
            "humidity": float(humidity),
            "sound": float(sound),
            "score": float(score),
            "is_anomaly": bool(is_anomaly)})

