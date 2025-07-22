import hashlib
import pandas as pd
import numpy as np
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

_engine = None
SessionLocal = None

def get_engine():
    global _engine, SessionLocal
    if _engine is None:
        user = os.environ.get("DB_USER", "postgres")
        password = os.environ.get("DB_PASSWORD", "mypassword")
        host = os.environ.get("DB_HOST", "postgres")
        port = os.environ.get("DB_PORT", "5432")
        db = os.environ.get("DB_NAME", "mydb")
        url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
        _engine = create_engine(url, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=_engine)
    return _engine

def create_table():
    """Creates table in the database"""
    engine = get_engine()
    create_script = """
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            station_id TEXT,
            timestamp TIMESTAMP,
            temperature FLOAT,
            humidity FLOAT,
            sound_volume FLOAT,
            anomaly_score FLOAT,
            is_anomaly BOOLEAN
        )
    """
    with engine.begin() as conn:
        conn.execute(text(create_script))
        
def get_session():
    if SessionLocal is None:
        raise RuntimeError("Database is not initialized")
    return SessionLocal()

def insert_prediction(station_id, timestamp, temp, humidity, sound, score, is_anomaly):
    """Inserts a new prediction into the database using a session"""
    session = get_session()
    try:
        insert_query = text("""
            INSERT INTO predictions (
                station_id, timestamp, temperature, humidity,
                sound_volume, anomaly_score, is_anomaly
            )
            VALUES (
                :station_id, :timestamp, :temp, :humidity,
                :sound, :score, :is_anomaly
            );
        """)
        session.execute(insert_query, {
            "station_id": station_id,
            "timestamp": timestamp,
            "temp": float(temp),
            "humidity": float(humidity),
            "sound": float(sound),
            "score": float(score),
            "is_anomaly": bool(is_anomaly)
        })
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        print("Insert failed:", e)
    finally:
        session.close()

def load_training_data(start_ts: str, end_ts: str):
    """Load rows between start_ts and end_ts (inclusive) from the database"""
    get_engine()  # Ensure engine and session are initialized
    session = get_session()
    query = text("""
        SELECT id, timestamp,
               temperature AS "Temperature_Readings",
               humidity AS "Humidity_Levels",
               sound_volume AS "Acoustic_Signals"
        FROM predictions
        WHERE timestamp BETWEEN :start AND :end
        ORDER BY timestamp
    """)
    try:
        df = pd.read_sql(query, session.bind, params={"start": start_ts, "end": end_ts})
        metadata = {
            "row_count": len(df),
            "row_id_min": df["id"].min(),
            "row_id_max": df["id"].max(),
            "data_hash": hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values.tobytes()).hexdigest(),
            "start_time": start_ts,
            "end_time": end_ts
        }
        return df.drop(columns=["id", "timestamp"]), metadata
    except Exception as e:
        print("Failed to load data:", e)
        return pd.DataFrame(), {}
    finally:
        session.close()

def init_db():
    get_engine()
    create_table()