from flask import Flask, Response
from prometheus_client import  generate_latest, CONTENT_TYPE_LATEST
from kafka_consumer import listen_to_model_update, listen_to_sensor_data
import threading

app = Flask(__name__)

@app.route("/")
def home():
    return "Model service is running"

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    threading.Thread(target=listen_to_sensor_data, daemon=True).start()
    threading.Thread(target=listen_to_model_update, daemon=True).start()
    app.run(host="0.0.0.0", port=8000, use_reloader=False)
