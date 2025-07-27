import pandas as pd
from db import save_prediction
from metrics import anomaly_counter, score_gauge

def handle_prediction(data, model):
    try:
        temp = float(data.get("Temperature_Readings"))
        humidity = float(data.get('Humidity_Levels'))
        sound = float(data.get('Acoustic_Signals'))
        station_id=data.get("station_id")
        timestamp=data.get("timestamp")

        features={
            "Temperature_Readings":temp,
            "Humidity_Levels":humidity,
            "Acoustic_Signals":sound
        }
        # Predict with the model
        features=pd.DataFrame([features])
        score = model.decision_function(features)[0]
        prediction = model.predict(features)[0]
        is_anomaly = prediction == -1
        # Save prediction to the db
        save_prediction(station_id, timestamp, temp, humidity,sound, score, is_anomaly)
        # Update Prometheus metrics
        score_gauge.labels(station_id=station_id).set(score)
        if is_anomaly:
            anomaly_counter.labels(station_id=station_id).inc()

        print(f"Prediction: {prediction}, Score: {score}",flush=True)
    except Exception as e:
        print(f"Prediction failed: {e}")
