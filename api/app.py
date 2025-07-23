from flask import Flask, request, jsonify, Response, render_template_string, redirect, url_for
from scipy.stats import ks_2samp
import datetime
import pandas as pd
from db import insert_prediction,load_training_data
from monitor import *
from predictor import AnomalyDetector
from db import get_engine

def check_ks_drift(reference_df,production_df,threshold=0.05):
    """Checks drift in input data using Kolmogorov-Smirnov test"""
    drift_result={}
    features=["Temperature_Readings","Humidity_Levels","Acoustic_Signals"]
    for feature in features:
        stat,p_value=ks_2samp(reference_df[feature],production_df[feature])
        drift_result[feature]={
            "statistic":stat,
            "p_value":p_value,
            "drift":bool(p_value<threshold)
        }
    return drift_result

# Global state to track active anomalies count
active_anomalies_state = {}

def update_metrics(station_id, is_anomaly, score):
    """Updates Prometheus metrics"""
    prediction_counter.labels(station_id=station_id).inc()
    score_gauge.labels(station_id=station_id).set(score)
    current_count = active_anomalies_state.get(station_id, 0)
    if is_anomaly:
        anomaly_counter.labels(station_id=station_id).inc()
        current_count += 1
    else:
        current_count = max(current_count - 1, 0)
    active_anomalies_state[station_id] = current_count
    active_anomalies.labels(station_id=station_id).set(current_count)

def create_app():
    app=Flask(__name__)
    model=AnomalyDetector()
    get_engine()
    
    @app.route("/")
    def home():
        return render_template_string('''
            <h1> Anomaly Detection API</h1>
            <form action="/check_drift" method="post">
                <button type="submit">Check Drift</button>
            </form>
            <form action="/retrain" method="post">
                <button type="submit">Retrain Model</button>
            </form>
            <form action="/health" method="get">
                <button type="submit">Health</button>
            </form>
        ''')

    @app.route("/predict", methods=["POST"])
    @request_latency.time()
    def predict():
        try:
            data = request.get_json() 
            # Missing sensor field check
            required_fields=["Temperature_Readings",'Humidity_Levels','Acoustic_Signals', "station_id", "timestamp"]
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing field: {field}"}),400

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
            score = model.predict_score(features)[0]
            prediction = model.predict(features)[0]
            is_anomaly = prediction == -1

            # Insert prediction to the database
            insert_prediction(station_id, timestamp, temp, humidity, sound, score, is_anomaly)

            # Update prometheus metrics
            update_metrics(station_id, is_anomaly, score)

            return jsonify({
                "anomaly_score": float(score),
                "is_anomaly": bool(is_anomaly),
                "model_version": model.version
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/check_drift", methods=["POST"])
    def check_drift():
        try:
            params, reference_df=model.get_model_parameters() # Load the latest model parameters and training data

            end = datetime.datetime.utcnow()
            start = end - datetime.timedelta(days=7)

            production_df, metadata= load_training_data(start.isoformat(), end.isoformat())
            if reference_df.empty or production_df.empty:
                return jsonify({
                    "drift_detected":None,
                    "reason":"Reference or production data is empty",
                    "drift_details":{}
                }),200
            # Run KS test
            drift=check_ks_drift(reference_df,production_df)
            drift_detected=any(d['drift'] for d in drift.values())

            return jsonify({
                "drift_detected":bool(drift_detected),
                "drift_details":drift
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/retrain", methods=["POST"])
    def retrain():
        try:
            end = datetime.datetime.utcnow()
            start = end - datetime.timedelta(days=7) # production window = 7 days
            production_df, metadata= load_training_data(start.isoformat(), end.isoformat())
            model.train(production_df, metadata)
            return jsonify({"model_retrained": bool(True)})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/metrics")
    def metrics():
        return Response(get_metrics(), mimetype="text/plain")

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "ok",
            "model_name": model.model_name,
            "model_version": model.version})
    
    return app

if __name__ == "__main__":
    app=create_app()
    app.run(host="0.0.0.0", port=8000,debug=True)



